
import os
from dotenv import load_dotenv

load_dotenv()

ISO_BIND_HOST = os.getenv("ISO_BIND_HOST", "0.0.0.0")
ISO_BIND_PORT = int(os.getenv("ISO_BIND_PORT", "8583"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-render-app.onrender.com/iso-webhook")
HMAC_SECRET = os.getenv("HMAC_SECRET", "change-this-secret")
HMAC_HEADER = os.getenv("HMAC_HEADER", "X-Gateway-Signature")
DB_URL = os.getenv("DB_URL", "sqlite:///gateway.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
WEBHOOK_MAX_RETRIES = int(os.getenv("WEBHOOK_MAX_RETRIES", "5"))
WEBHOOK_BACKOFF_SECONDS = float(os.getenv("WEBHOOK_BACKOFF_SECONDS", "2.0"))
ISO_SPEC_PATH = os.getenv("ISO_SPEC_PATH", "")
MONITOR_BIND_HOST = os.getenv("MONITOR_BIND_HOST", "0.0.0.0")
MONITOR_BIND_PORT = int(os.getenv("MONITOR_BIND_PORT", "8080"))
