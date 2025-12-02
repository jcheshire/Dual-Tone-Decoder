from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from backend.core.database import Base


class ToneEntry(Base):
    __tablename__ = "tone_entries"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False, index=True)
    tone1_hz = Column(Float, nullable=False)
    tone2_hz = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ToneEntry(label='{self.label}', tone1={self.tone1_hz}Hz, tone2={self.tone2_hz}Hz)>"
