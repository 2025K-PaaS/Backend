# models/analysis.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from db.base import Base

class Analysis(Base):
    __tablename__ = "analysis"
    __table_args__ = (
        Index("ix_analysis_username", "username"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_analysis_id = Column(String(40), unique=True, index=True, nullable=False)

    username = Column(String(50), nullable=False)

    detected_item = Column(String(100))
    material_type = Column(String(50))
    suggested_title = Column(String(100))
    image_path = Column(Text) 

    estimated_value = Column(Integer)     
    status = Column(String(20), default="pending", nullable=False)  # pending | used | expired

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
