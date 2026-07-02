from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    party1_name = Column(String, nullable=False)
    party1_email = Column(String, nullable=True)
    party1_phone = Column(String, nullable=True)
    party1_address = Column(String, nullable=False)
    party2_name = Column(String, nullable=False)
    party2_email = Column(String, nullable=True)
    party2_phone = Column(String, nullable=True)
    party2_address = Column(String, nullable=False)
    issue = Column(Text, nullable=False)
    template = Column(String, nullable=True)
    draft_text = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, nullable=True)