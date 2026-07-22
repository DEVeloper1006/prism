"""Smart collection endpoints."""

from fastapi import APIRouter, HTTPException

from models.schemas import CollectionCreate

router = APIRouter(tags=["collections"])


@router.get("/collections")
async def list_collections():
    from main import get_store

    store = get_store()
    if store is None:
        return []
    return store.list_collections()


@router.post("/collections")
async def create_collection(coll: CollectionCreate):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    coll_id = store.insert_collection(coll.name, coll.rules)
    store.log_action("collection_create", coll.name)
    return {"id": coll_id}


@router.get("/collections/{collection_id}/clips")
async def collection_clips(collection_id: int):
    from main import get_store

    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="No project loaded")
    return store.get_collection_clips(collection_id)
