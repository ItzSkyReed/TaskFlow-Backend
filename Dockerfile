FROM python:3.13-slim

RUN pip install --no-cache-dir uv

COPY pyproject.toml .

RUN uv pip install -r pyproject.toml --system

WORKDIR /fast_api

COPY ./src /fast_api/src
COPY ./alembic.ini /fast_api/alembic.ini
COPY ./alembic /fast_api/alembic

EXPOSE 8000

CMD ["fastapi", "dev", "app/main.py", "--host", "0.0.0.0"]