from pathlib import Path

log_path = Path(__file__).resolve().parent.parent / "logs"
log_path.mkdir(parents=True, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] — %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": str(log_path / "server.log"),
            "mode": "a",
            "level": "WARNING",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "WARNING",
        },
        "uvicorn.access": {
            "level": "INFO",
        },
        "sqlalchemy.engine": {
            "level": "WARNING",
        },
    },
}
