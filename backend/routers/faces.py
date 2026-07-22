"""Face cluster endpoints."""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["faces"])


@router.get("/faces")
async def list_faces():
    from main import get_store

    store = get_store()
    if store is None:
        return []
    return store.list_face_clusters()


@router.get("/faces/{cluster_id}/clips")
async def face_clips(cluster_id: int):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    return store.get_clips_for_face(cluster_id)
