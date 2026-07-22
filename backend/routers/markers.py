"""Marker endpoints."""

from fastapi import APIRouter, HTTPException

from models.schemas import MarkerCreate, MarkerResponse

router = APIRouter(tags=["markers"])


@router.post("/markers")
async def create_marker(marker: MarkerCreate):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    marker_id = store.insert_marker(marker.model_dump())
    store.log_action("marker_create", f"clip={marker.clip_id} t={marker.timestamp_seconds}")
    return {"id": marker_id}


@router.get("/markers/{clip_id}")
async def get_markers(clip_id: str):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    return store.get_markers(clip_id)
