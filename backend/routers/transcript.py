"""Transcript endpoints."""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["transcript"])


@router.get("/transcript/{clip_id}")
async def get_transcript(clip_id: str):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    return store.get_transcript(clip_id)
