.PHONY: install run test smoke clean

install:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate 2>/dev/null; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	. .venv/bin/activate 2>/dev/null; pytest -q

smoke:
	. .venv/bin/activate 2>/dev/null; pytest -q tests/test_smoke.py

clean:
	rm -f *.sqlite *.db memstore.db
	find . -name __pycache__ -type d -exec rm -rf {} +
