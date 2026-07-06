FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock .python-version ./
COPY shared/ shared/
COPY agent/ agent/
COPY backend/pyproject.toml backend/pyproject.toml
RUN mkdir -p backend/src/bankagent_backend && touch backend/src/bankagent_backend/__init__.py \
    && uv sync --frozen --no-dev --package bankagent-agent

FROM python:3.13-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY --from=builder /app/shared shared
COPY --from=builder /app/agent agent
ENV PATH="/app/.venv/bin:$PATH"
# Turn-detector / VAD model weights baked into the image.
RUN python -m livekit.agents download-files
CMD ["python", "-m", "bankagent_agent.main", "start"]
