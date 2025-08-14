
import asyncio, logging, json, os
import httpx
from pyiso8583 import iso8583
from pyiso8583.specs import default_ascii as iso_spec
from .config import ISO_BIND_HOST, ISO_BIND_PORT, WEBHOOK_URL, HMAC_SECRET, HMAC_HEADER, WEBHOOK_MAX_RETRIES, WEBHOOK_BACKOFF_SECONDS, ISO_SPEC_PATH, LOG_LEVEL
from .models import init_db, SessionLocal, Message, WebhookResult
from .utils import compute_hmac, idem_key_from_fields, to_hex, json_dumps

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("iso-gateway")
init_db()

class IsoGatewayServer:
    async def start(self):
        server = await asyncio.start_server(self.handle_client, ISO_BIND_HOST, ISO_BIND_PORT)
        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        logger.info(f"Listening on {addrs}")
        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        peer = writer.get_extra_info("peername")
        logger.info(f"Connection from {peer}")
        try:
            while True:
                hdr = await reader.readexactly(2)
                msg_len = int.from_bytes(hdr, "big")
                payload = await reader.readexactly(msg_len)
                await self.process_iso_message(payload, peer)
        except asyncio.IncompleteReadError:
            logger.info(f"Peer {peer} closed.")
        finally:
            writer.close()
            await writer.wait_closed()

    async def process_iso_message(self, payload, peer):
        try:
            iso = iso8583.ISO8583(iso_spec)
            iso.set_network_iso(payload)
            iso.parse()
            mti = iso.get_mti()
            fields = {k: iso.get_bit(k) for k in iso.get_bits()}
        except Exception as e:
            logger.exception(f"Parse error from {peer}: {e}")
            return

        f37, f11, f41, f42, f39, f4, f49 = (fields.get(k,"") for k in ["37","11","41","42","39","4","49"])
        arn = fields.get("62","")
        idem = idem_key_from_fields(mti, f37, f11, f41, f42)

        sess = SessionLocal()
        try:
            msg = Message(direction="in", remote_addr=str(peer), raw_hex=to_hex(payload), mti=mti, f11=f11, f37=f37, f41=f41, f42=f42, f39=f39, f4=f4, f49=f49, arn=arn, parsed_json=json_dumps(fields), idem_key=idem)
            sess.add(msg); sess.commit()
        except Exception as e:
            sess.rollback()
            logger.warning(f"DB write issue: {e}")
        finally:
            sess.close()

        if mti != "0210":
            return

        payload_json = {"mti": mti, "39": f39, "4": f4, "37": f37, "11": f11, "41": f41, "42": f42, "49": f49, "arn": arn}
        body = json.dumps(payload_json).encode()
        sig = compute_hmac(body, HMAC_SECRET)

        sess = SessionLocal()
        try:
            out_msg = Message(direction="out", remote_addr="webhook", mti=mti, f11=f11, f37=f37, f41=f41, f42=f42, f39=f39, f4=f4, f49=f49, arn=arn, parsed_json=json_dumps(payload_json), idem_key=idem)
            sess.add(out_msg); sess.commit()
            msg_id = out_msg.id
        except Exception:
            sess.rollback()
            msg_id = None
        finally:
            sess.close()

        if not msg_id:
            return

        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(1, WEBHOOK_MAX_RETRIES+1):
                try:
                    resp = await client.post(WEBHOOK_URL, headers={"Content-Type":"application/json", HMAC_HEADER: sig}, content=body)
                    await self.record_result(msg_id, resp.status_code, resp.text, "", attempt)
                    if 200 <= resp.status_code < 300:
                        break
                except Exception as e:
                    await self.record_result(msg_id, 0, "", str(e), attempt)
                await asyncio.sleep(WEBHOOK_BACKOFF_SECONDS * attempt)

    async def record_result(self, msg_id, status, body, err, attempt):
        sess = SessionLocal()
        try:
            wr = WebhookResult(message_id=msg_id, url=WEBHOOK_URL, status_code=status, response_body=body, error=err, attempt=attempt)
            sess.add(wr); sess.commit()
        except Exception as e:
            sess.rollback()
            logger.error(f"Result store error: {e}")
        finally:
            sess.close()

def main():
    asyncio.run(IsoGatewayServer().start())

if __name__ == "__main__":
    main()
