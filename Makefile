# Optional: .env vars visible to make itself (fresh clones/CI have no .env).
# The services read .env themselves, so this is convenience, not a requirement.
-include .env
.PHONY: setup dev run-agent run-backend run-frontend lint format typecheck \
        test test-cov test-behavioral docker-up clean

# This machine's ~/.local/share is root-owned; keep uv's managed Pythons in a
# user-writable location. Harmless on machines where the default works.
export UV_PYTHON_INSTALL_DIR := $(HOME)/.uv/python
SECRETS_FILE ?= .env

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
setup: ## Install Python + frontend deps, model weights, git hooks
	uv sync --all-packages
	npm install --prefix frontend
	uv run python -m livekit.agents download-files
	uv run pre-commit install

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
dev: ## Run backend + agent + frontend together (hot reload)
	uv run honcho start

run-backend:
	uv run uvicorn bankagent_backend.app:create_app --factory --reload --port 8000

run-agent:
	uv run python -m bankagent_agent.main dev

run-frontend:
	npm run dev --prefix frontend

console: ## Talk to the agent in the terminal (no browser/frontend needed)
	uv run python -m bankagent_agent.main console

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------
lint:
	uv run ruff check .
	uv run ruff format --check .
	npm run lint --prefix frontend

format:
	uv run ruff format .
	uv run ruff check --fix .
	npm run format --prefix frontend

typecheck:
	uv run mypy
	npm run typecheck --prefix frontend

test: ## Unit tests (no credentials needed)
	uv run pytest

test-cov:
	uv run pytest --cov --cov-report=term-missing

test-behavioral: ## Agent-behavior tests against a live LLM (needs LIVEKIT_* creds)
	uv run pytest -m behavioral --reruns 1

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
docker-up:
	docker compose --profile frontend up --build

# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------
clean:
	rm -rf .venv .mypy_cache .ruff_cache .pytest_cache .coverage htmlcov
	rm -rf frontend/node_modules frontend/dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
