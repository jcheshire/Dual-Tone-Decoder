from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ToneEntryBase(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    tone1_hz: float = Field(..., gt=0, description="First tone frequency in Hz")
    tone2_hz: float = Field(..., gt=0, description="Second tone frequency in Hz")


class ToneEntryCreate(ToneEntryBase):
    pass


class ToneEntryUpdate(ToneEntryBase):
    pass


class ToneEntryResponse(ToneEntryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ToneDetectionResult(BaseModel):
    tone1_detected_hz: Optional[float] = None
    tone2_detected_hz: Optional[float] = None
    matched_entry: Optional[ToneEntryResponse] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    message: str
