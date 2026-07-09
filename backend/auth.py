import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("[AUTH]")


class TokenAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token: str) -> None:  # noqa: ANN001
        super().__init__(app)
        self.token = token

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        if request.url.path == "/health":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header != f"Bearer {self.token}":
            logger.warning("Rejected request with invalid token")
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        return await call_next(request)
