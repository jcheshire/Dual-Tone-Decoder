from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class ToneEntryBase(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    tone1_hz: float = Field(..., gt=0, le=20000, description="First tone frequency in Hz (max 20kHz)")
    tone2_hz: float = Field(..., gt=0, le=20000, description="Second tone frequency in Hz (max 20kHz)")

    @field_validator('label')
    @classmethod
    def sanitize_label(cls, v: str) -> str:
        """Sanitize label to prevent XSS and ensure printable characters."""
        # Remove any HTML/script tags
        v = re.sub(r'<[^>]*>', '', v)
        # Remove non-printable characters except spaces
        v = ''.join(char for char in v if char.isprintable() or char.isspace())
        # Strip leading/trailing whitespace
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Label must contain at least one printable character')
        return v

    @field_validator('tone1_hz', 'tone2_hz')
    @classmethod
    def validate_frequency(cls, v: float) -> float:
        """Ensure frequency is within reasonable audio range."""
        if v < 20 or v > 20000:
            raise ValueError('Frequency must be between 20Hz and 20kHz')
        return v


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
