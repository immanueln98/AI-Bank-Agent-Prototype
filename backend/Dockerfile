FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock .python-version ./
COPY shared/ shared/
COPY backend/ backend/
COPY agent/pyproject.toml agent/pyproject.toml
RUN mkdir -p agent/src/bankagent_agent && touch agent/src/bankagent_agent/__init__.py \
    && uv sync --frozen --no-dev --package bankagent-backend

FROM python:3.13-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY --from=builder /app/shared shared
COPY --from=builder /app/backend backend
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "bankagent_backend.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
