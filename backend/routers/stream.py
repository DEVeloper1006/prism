"""WebSocket streaming endpoints for progress and watch events."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["stream"])


@router.websocket("/ws/progress")
async def ws_progress(websocket: WebSocket):
    from main import get_ws_manager

    manager = get_ws_manager()
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/watch")
async def ws_watch(websocket: WebSocket):
    from main import get_ws_manager

    manager = get_ws_manager()
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
