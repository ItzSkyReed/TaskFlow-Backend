import asyncio
import logging.config
import os
import sys
from pathlib import Path
from typing import TypedDict

from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from .auth import auth_router
from .config import get_settings
from .groups import group_router
from .logging_config import LOGGING_CONFIG

# To correctly load all models
from .models import *  # noqa: F401, F403
from .user import profile_router

BASE_DIR = Path(os.getcwd())  # project_root

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

settings = get_settings()


class ExtraAppConfig(TypedDict, total=False):
    docs_url: str | None
    redoc_url: str | None
    openapi_url: str | None


if sys.platform != "win32" and settings.environment != "TEST":
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logger.info("uvloop enabled")


def create_app() -> FastAPI:
    docs_settings: ExtraAppConfig = {}
    if settings.environment != "PROD":
        docs_settings = {
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "openapi_url": "/openapi.json",
        }

    fast_api_app = FastAPI(
        root_path="/task_flow",
        title=settings.project_name,
        version=settings.version,
        default_response_class=ORJSONResponse,
        **docs_settings,
    )

    # CORS
    fast_api_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Healthcheck
    @fast_api_app.get("/health", include_in_schema=False)
    async def health_check():
        return PlainTextResponse("OK")

    # API Router
    api_router = APIRouter(prefix=settings.api_prefix)
    api_router.include_router(auth_router)
    api_router.include_router(profile_router)
    api_router.include_router(group_router)
    fast_api_app.include_router(api_router)

    return fast_api_app


app = create_app()
