# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Meridian Bank — AI voice agent proof-of-concept for a retail-bank call centre, built on LiveKit Agents. A customer talks to the agent in the browser (or by phone via SIP); the agent verifies identity, answers balance/transaction questions, blocks cards, files disputes, and escalates to a human with a summary. The "core banking system" is a mock FastAPI service with fixture data — no real customer data or money movement.

## Commands

The Makefile is the canonical interface. Python is managed by `uv` (workspace), frontend by `npm`.

- `make setup` — `uv sync --all-packages`, `npm install --prefix frontend`, model weights, pre-commit hooks
- `make dev` — all three services via honcho (backend :8000, agent worker, frontend :5173)
- `make run-backend` / `make run-agent` / `make run-frontend` — one service at a time
- `make console` — terminal voice/text chat with the agent (backend must already be running)
- `make lint` / `make format` / `make typecheck` — ruff + mypy (strict) for Python, eslint/prettier/tsc for frontend
- `make test` — unit tests only; behavioral tests are excluded by default (`addopts = "-m 'not behavioral'"`)
- Single test: `uv run pytest backend/tests/test_customers.py::test_name` or `uv run pytest agent/tests -k <expr>`
- `make test-behavioral` — `uv run pytest -m behavioral --reruns 1`; drives the real agents with a real LLM through LiveKit's in-process harness (no STT/TTS, stubbed bank client). Requires `LIVEKIT_*` creds in `.env`; skips without them; costs pennies per run.
- `make setup-sip NUMBERS=+27... [AUTH=user:pass]` — provisions the LiveKit inbound SIP trunk + agent dispatch rule (`scripts/setup_sip.py`, safe to re-run)

## Architecture

uv workspace of three Python packages plus a React frontend. Data flow:

Browser demo console (React/Vite) ⇄ LiveKit Cloud WebRTC room ⇄ agent worker (livekit-agents; STT/LLM/TTS via LiveKit Inference) → mock banking backend over HTTP. The browser obtains its LiveKit token by POSTing to the backend (`livekit_token` router).

- `shared/` (`bankagent_shared`) — Pydantic API models (`models.py`), PII redaction (`redaction.py`), structlog setup, event types. This is the integration contract between agent and backend.
- `backend/` (`bankagent_backend`) — mock core-banking FastAPI app. Entry: `app.py` `create_app()` factory. Routers in `routers/` mounted at `/api/v1` (customers, cards, disputes, faq, escalations, calls, transcripts, demo, livekit_token). `fixtures.py` holds the 5 demo customers — the only file to edit to change demo data.
- `agent/` (`bankagent_agent`) — voice worker. Entry: `python -m bankagent_agent.main {dev|console|start}`. Two agents in `agents/`: `IdentityAgent` (has no account tools — the structural identity gate) hands off to `BankingAgent` (account tools) only after `verify_identity` succeeds. `config.py` holds `AgentSettings` plus the `build_llm`/`build_stt`/`build_tts` factories — the one file to change to swap providers. Supporting modules: `bank_client.py` (httpx + tenacity retries), `events.py` (PII-masked `ToolEventEmitter`, streamed to the browser over the `tool-events` text stream), `transcripts.py` (masked JSONL under `transcripts/<date>/`), `latency.py`, `session_state.py` (holds the `verified` flag).
- `frontend/` — React 19 + Vite demo console (`CallPanel`, `ActivityPanel`, `SupervisorPanel`, `ScenarioPicker`). Vite proxies `/api` to the backend and allows ngrok-free.dev hosts (`ngrok http 5173` shares the whole demo).

Invariants to preserve:

- The agent touches banking data only through the backend's HTTP API. Replacing fixture routers with real adapters must leave agent code unchanged.
- `IdentityAgent` must never gain account tools; `agent/tests/test_tool_schemas.py` asserts this structurally, and `agent/tests/behavioral/` verifies the gate end-to-end.
- Named/explicit dispatch: the worker, the token endpoint, and the SIP dispatch rule all share `AGENT_NAME` (default `meridian-bank-agent`). Run only one agent worker at a time on the free LiveKit plan.
- Tool events and transcripts are PII-masked (via `shared` redaction) before leaving the process; the supervisor view reads the masked transcripts directory.

## Configuration

Everything is env-driven via `.env` (copy from `.env.example`): `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` (also authenticate LiveKit Inference), `LLM_PROVIDER` (`inference` default, or `anthropic` + `ANTHROPIC_API_KEY`), `LLM_MODEL`, `STT_MODEL`, `TTS_MODEL`, `TTS_VOICE`, `AGENT_NAME`, `BACKEND_BASE_URL`, `LOG_FORMAT` (`console` locally, `json` in containers). The frontend reads `frontend/.env.local` (`VITE_BACKEND_URL`).

## Conventions

- Python 3.13 (`.python-version`); pyproject allows >=3.12,<3.14 and ruff/mypy target py312.
- ruff line-length 100; mypy strict (`disallow_untyped_defs` etc.); pre-commit runs ruff + ruff-format + mypy.
- pytest: `asyncio_mode = "auto"`, `--import-mode=importlib`, testpaths are `shared/tests`, `backend/tests`, `agent/tests`.
- CI (`.github/workflows/ci.yml`): `python` and `frontend` (Node 22) jobs on every push/PR; `behavioral` job only on pushes to main or manual dispatch (needs `LIVEKIT_*` secrets).
