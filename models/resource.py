# models/resource.py
from sqlalchemy import Column, Integer, Text, String, Float, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from db.base import Base
import enum

class ResourceStatus(str, enum.Enum):
    registered = "registered"  # 등록 완료
    matched    = "matched"     # 매칭됨(거래 확정 전)
    completed  = "completed"   # 거래 완료

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("analysis.id"))

    title = Column(String(100), nullable=False)
    description = Column(Text)
    amount = Column(Float, nullable=False, default=0)
    unit = Column(String(10), nullable=True)
    value = Column(Integer, nullable=False, default=0) 

    detected_item = Column(String(100), index=True)
    material_type = Column(String(50), index=True)
    status = Column(
        Enum(ResourceStatus, native_enum=False),   
        nullable=False,
        default=ResourceStatus.registered,
        server_default=ResourceStatus.registered.value,
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis = relationship("Analysis")

Index("ix_resources_unit_status", Resource.unit, Resource.status)
