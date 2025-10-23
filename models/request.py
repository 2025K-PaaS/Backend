# models/request.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.base import Base

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    wanted_item = Column(String(100), nullable=False, index=True)
    material_type = Column(String(50), index=True)
    desired_amount = Column(Float, nullable=False)
    unit = Column(String(10), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(20), default="open", index=True)  # open | matched | completed

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="requests", lazy="joined")
