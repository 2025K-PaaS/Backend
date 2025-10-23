# models/analysis.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from db.base import Base

class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_analysis_id = Column(String(40), unique=True, index=True, nullable=False)  # 외부 AI ID
    username = Column(String(50), nullable=False)

    detected_item = Column(String(100))
    material_type = Column(String(50))
    suggested_title = Column(String(100))
    image_path = Column(Text)   # (선택) 프록시 업로드 시 로컬 저장 경로

    created_at = Column(DateTime, default=datetime.utcnow)

Index("ix_analysis_username", Analysis.username)