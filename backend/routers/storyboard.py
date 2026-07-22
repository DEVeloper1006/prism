"""Storyboard endpoints."""

from fastapi import APIRouter, HTTPException

from models.schemas import StoryboardCreate, StoryboardUpdate

router = APIRouter(tags=["storyboard"])


@router.post("/storyboard")
async def create_storyboard(sb: StoryboardCreate):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    sb_id = store.insert_storyboard(sb.name, sb.mode, sb.cells)
    store.log_action("storyboard_create", sb.name)
    return {"id": sb_id}


@router.get("/storyboard/{storyboard_id}")
async def get_storyboard(storyboard_id: int):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    sb = store.get_storyboard(storyboard_id)
    if not sb:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    return sb


@router.put("/storyboard/{storyboard_id}")
async def update_storyboard(storyboard_id: int, update: StoryboardUpdate):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    store.update_storyboard(storyboard_id, name=update.name, cells=update.cells)
    return {"status": "updated"}


@router.post("/storyboard/{storyboard_id}/generate")
async def generate_storyboard(storyboard_id: int):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    sb = store.get_storyboard(storyboard_id)
    if not sb:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    return sb
