
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DB_URL

Base = declarative_base()

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    direction = Column(String(8))
    remote_addr = Column(String(64))
    raw_hex = Column(Text)
    mti = Column(String(4))
    f11 = Column(String(12))
    f37 = Column(String(12))
    f41 = Column(String(16))
    f42 = Column(String(32))
    f39 = Column(String(2))
    f4  = Column(String(16))
    f49 = Column(String(3))
    arn = Column(String(24))
    parsed_json = Column(Text)
    idem_key = Column(String(128), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('idem_key', name='uq_idem_key'),)

class WebhookResult(Base):
    __tablename__ = "webhook_results"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, index=True)
    url = Column(String(256))
    status_code = Column(Integer)
    response_body = Column(Text)
    error = Column(Text)
    attempt = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(DB_URL, echo=False, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(engine)
