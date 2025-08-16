import asyncio
import logging.config
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TypedDict

from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from .auth import auth_router
from .config import get_settings
from .logging_config import LOGGING_CONFIG

# To correctly load all models
from .models import *  # noqa: F401, F403
from .user import profile_router

# uvloop быстрее стандартного event loop
if sys.platform != "win32":
    # noinspection PyUnresolvedReferences
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

BASE_DIR = Path(os.getcwd())  # project_root

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)

settings = get_settings()


class ExtraAppConfig(TypedDict, total=False):
    docs_url: str | None
    redoc_url: str | None
    openapi_url: str | None


docs_settings: ExtraAppConfig = {}
if settings.environment != "PROD":
    extra_config: ExtraAppConfig = {
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }

app = FastAPI(
    root_path="/task_flow",
    title=settings.project_name,
    version=settings.version,
    default_response_class=ORJSONResponse,
    **docs_settings,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# For healthcheck
@app.get("/health", include_in_schema=False)
async def health_check():
    return PlainTextResponse("OK")


api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(auth_router)
api_router.include_router(profile_router)

app.include_router(api_router)
