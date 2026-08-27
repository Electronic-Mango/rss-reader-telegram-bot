# Dockerfile which can be used for deploying the bot as a Docker container.

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_NO_DEV=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY .python-version pyproject.toml uv.lock ./
COPY src ./src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

COPY *.yml ./

CMD ["uv", "run", "./src/main/main.py"]
