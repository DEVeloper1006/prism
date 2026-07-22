"""Watch folder endpoints."""

from fastapi import APIRouter, HTTPException

from models.schemas import WatchConfigRequest

router = APIRouter(tags=["watch"])


@router.get("/watch")
async def get_watch_status():
    from main import get_store

    store = get_store()
    if store is None:
        return {"folder_path": None, "active": False, "last_scan": None}
    config = store.get_watch_config()
    if not config:
        return {"folder_path": None, "active": False, "last_scan": None}
    return config


@router.post("/watch/configure")
async def configure_watch(req: WatchConfigRequest):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    store.set_watch_config(req.folder_path, req.active)
    store.log_action("watch_configure", f"path={req.folder_path} active={req.active}")
    return {"status": "configured"}
