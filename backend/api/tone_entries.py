from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
from backend.core.database import get_db
from backend.core.rate_limit import limiter
from backend.models.tone_table import ToneEntry
from backend.models.schemas import (
    ToneEntryCreate,
    ToneEntryUpdate,
    ToneEntryResponse
)

router = APIRouter(prefix="/api/tones", tags=["tone_entries"])


@router.get("/", response_model=List[ToneEntryResponse])
async def list_tone_entries(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all tone entries."""
    # Validate and cap query parameters to prevent abuse
    if skip < 0:
        skip = 0
    if limit < 1:
        limit = 100
    if limit > 1000:  # Cap maximum results
        limit = 1000

    result = await db.execute(
        select(ToneEntry).offset(skip).limit(limit)
    )
    entries = result.scalars().all()
    return entries


@router.get("/{entry_id}", response_model=ToneEntryResponse)
async def get_tone_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific tone entry by ID."""
    result = await db.execute(
        select(ToneEntry).where(ToneEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tone entry with id {entry_id} not found"
        )

    return entry


@router.post("/", response_model=ToneEntryResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")  # Limit creation to prevent database spam
async def create_tone_entry(
    request: Request,
    entry: ToneEntryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tone entry."""
    db_entry = ToneEntry(
        label=entry.label,
        tone1_hz=entry.tone1_hz,
        tone2_hz=entry.tone2_hz
    )

    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)

    return db_entry


@router.put("/{entry_id}", response_model=ToneEntryResponse)
async def update_tone_entry(
    entry_id: int,
    entry: ToneEntryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing tone entry."""
    result = await db.execute(
        select(ToneEntry).where(ToneEntry.id == entry_id)
    )
    db_entry = result.scalar_one_or_none()

    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tone entry with id {entry_id} not found"
        )

    db_entry.label = entry.label
    db_entry.tone1_hz = entry.tone1_hz
    db_entry.tone2_hz = entry.tone2_hz

    await db.commit()
    await db.refresh(db_entry)

    return db_entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")  # Limit deletions
async def delete_tone_entry(
    request: Request,
    entry_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tone entry."""
    result = await db.execute(
        delete(ToneEntry).where(ToneEntry.id == entry_id)
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tone entry with id {entry_id} not found"
        )

    await db.commit()
    return None
