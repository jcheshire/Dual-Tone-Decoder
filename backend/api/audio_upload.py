from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
import os
import uuid
from typing import List
from backend.core.database import get_db
from backend.core.config import get_settings
from backend.models.tone_table import ToneEntry
from backend.models.schemas import ToneDetectionResult, ToneEntryResponse
from backend.services.tone_detector import ToneDetector

router = APIRouter(prefix="/api/decode", tags=["audio"])
settings = get_settings()


@router.post("/", response_model=ToneDetectionResult)
async def decode_audio(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an audio file and detect two-tone sequence.
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = settings.allowed_extensions.split(",")

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
        )

    # Save uploaded file temporarily
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = upload_dir / temp_filename

    try:
        # Write file
        with open(temp_path, "wb") as f:
            contents = await file.read()
            f.write(contents)

        # Detect tones
        detector = ToneDetector(tolerance_hz=settings.frequency_tolerance_hz)
        tone1_hz, tone2_hz, confidence = detector.detect_two_tone_sequence(str(temp_path))

        if tone1_hz is None or tone2_hz is None:
            return ToneDetectionResult(
                tone1_detected_hz=None,
                tone2_detected_hz=None,
                matched_entry=None,
                confidence=0.0,
                message="No two-tone sequence detected in audio file"
            )

        # Fetch all tone entries from database
        result = await db.execute(select(ToneEntry))
        entries = result.scalars().all()

        # Convert to format expected by detector
        tone_list = [(e.id, e.label, e.tone1_hz, e.tone2_hz) for e in entries]

        # Find matching entry
        matched = detector.find_matching_tone(tone1_hz, tone2_hz, tone_list)

        if matched:
            entry_id, label, _, _ = matched
            matched_entry_obj = next(e for e in entries if e.id == entry_id)
            matched_entry = ToneEntryResponse.model_validate(matched_entry_obj)
            message = f"Match found: {label}"
        else:
            matched_entry = None
            message = "Tones detected but no matching entry in database"

        return ToneDetectionResult(
            tone1_detected_hz=round(tone1_hz, 1),
            tone2_detected_hz=round(tone2_hz, 1),
            matched_entry=matched_entry,
            confidence=round(confidence, 2),
            message=message
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio file: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_path.exists():
            os.remove(temp_path)
