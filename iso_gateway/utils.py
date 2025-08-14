
import hmac, hashlib, binascii, json, re

MASK_PAN_RE = re.compile(r"^(\d{6})\d+(\d{4})$")

def compute_hmac(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

def mask_pan(pan: str) -> str:
    if not pan:
        return ""
    m = MASK_PAN_RE.match(pan)
    if not m:
        return pan[:1] + "*" * max(0, len(pan)-5) + pan[-4:]
    return f"{m.group(1)}******{m.group(2)}"

def idem_key_from_fields(mti: str, f37: str, f11: str, f41: str, f42: str) -> str:
    base = f"{mti}|{f37}|{f11}|{f41}|{f42}"
    return hashlib.sha256(base.encode()).hexdigest()

def to_hex(b: bytes) -> str:
    return binascii.hexlify(b).decode()

def json_dumps(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
