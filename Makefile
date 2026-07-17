.PHONY: init format check requirements test run

init:
	set -e; \
	installer="$$(mktemp)"; \
	trap 'rm -f "$$installer"' EXIT; \
	wget -qO "$$installer" https://astral.sh/uv/install.sh; \
	UV_INSTALL_DIR="$$HOME/.local/bin" sh "$$installer"; \
	PATH="$$HOME/.local/bin:$$PATH"; export PATH; \
	uv venv; \
	uv sync; \
	uvx pyrefly init; \
	uvx mypy --version

format:
	uvx ruff format src

check:
	uvx ruff check src --fix; \
	uvx ty check src; \
	uvx mypy src; \
	uvx pyrefly check

requirements:
	uv export -o requirements.txt --without-hashes --without dev
	uv export -o requirements-dev.txt --without-hashes

test:
	uv run pytest tests/ -v

run:
	uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
