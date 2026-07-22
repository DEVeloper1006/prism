"""Clip browsing and detail endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from models.schemas import ClipResponse

router = APIRouter(tags=["clips"])


@router.get("/clips")
async def list_clips(offset: int = 0, limit: int = 50):
    from main import get_store

    store = get_store()
    if store is None:
        return []
    return store.list_clips(offset=offset, limit=limit)


@router.get("/clips/{clip_id}")
async def get_clip(clip_id: str):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    clip = store.get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.get("/clips/{clip_id}/thumbnail")
async def get_thumbnail(clip_id: str):
    from main import get_prism_dir

    prism_dir = get_prism_dir()
    if prism_dir is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    thumb_path = prism_dir / "thumbs" / f"{clip_id}.webp"
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(str(thumb_path), media_type="image/webp")


@router.get("/clips/{clip_id}/keyframes")
async def get_keyframes(clip_id: str):
    from main import get_prism_dir

    prism_dir = get_prism_dir()
    if prism_dir is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    kf_dir = prism_dir / "keyframes" / clip_id
    if not kf_dir.exists():
        return []
    return sorted([str(p) for p in kf_dir.glob("*.jpg")])


@router.get("/clips/{clip_id}/waveform")
async def get_waveform(clip_id: str):
    from main import get_prism_dir

    prism_dir = get_prism_dir()
    if prism_dir is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    wf_path = prism_dir / "waveforms" / f"{clip_id}.json"
    if not wf_path.exists():
        return []
    import json
    return json.loads(wf_path.read_text())


@router.get("/clips/{clip_id}/palette")
async def get_palette(clip_id: str):
    from main import get_prism_dir

    prism_dir = get_prism_dir()
    if prism_dir is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    pal_path = prism_dir / "color_palettes" / f"{clip_id}.json"
    if not pal_path.exists():
        return []
    import json
    return json.loads(pal_path.read_text())


@router.get("/clips/{clip_id}/similar")
async def find_similar(clip_id: str, top_k: int = 10):
    from main import get_vector_store

    vs = get_vector_store()
    if vs is None:
        return []
    return vs.find_similar(clip_id, top_k=top_k)
