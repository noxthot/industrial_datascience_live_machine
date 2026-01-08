FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY .python-version readme.md pyproject.toml uv.lock /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
    
COPY ./dist /app

WORKDIR /app
CMD ["uv", "run", "opc-ua-server.py"]
