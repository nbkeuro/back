
from flask import Flask, render_template
from sqlalchemy import desc
from .models import SessionLocal, Message, WebhookResult, init_db
from .config import MONITOR_BIND_HOST, MONITOR_BIND_PORT

app = Flask(__name__)
init_db()

@app.route("/")
def dashboard():
    sess = SessionLocal()
    try:
        msgs = sess.query(Message).order_by(desc(Message.created_at)).limit(200).all()
        results = {}
        for r in sess.query(WebhookResult).order_by(desc(WebhookResult.created_at)).limit(500).all():
            results.setdefault(r.message_id, []).append(r)
    finally:
        sess.close()
    return render_template("dashboard.html", msgs=msgs, results=results)

def run():
    app.run(host=MONITOR_BIND_HOST, port=MONITOR_BIND_PORT)

if __name__ == "__main__":
    run()
