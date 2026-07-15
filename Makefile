.PHONY: install run test smoke clean

# Prefer python3.11 (pinned wheels don't yet build on 3.14); fall back to python3.
PYTHON := $(shell command -v python3.11 || command -v python3)

install:
	$(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate 2>/dev/null; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	. .venv/bin/activate 2>/dev/null; pytest -q

smoke:
	. .venv/bin/activate 2>/dev/null; pytest -q tests/test_smoke.py

clean:
	rm -f *.sqlite *.db memstore.db
	find . -name __pycache__ -type d -exec rm -rf {} +
