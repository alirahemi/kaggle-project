.PHONY: install lint test run-api run-ui docker-up docker-down ingest seed

install:
	pip install -r requirements.txt

lint:
	ruff check agents apps mcp_servers tests config scripts

test:
	pytest tests/ -v

run-api:
	uvicorn apps.api_gateway.main:app --reload --host 0.0.0.0 --port 8000

run-ui:
	streamlit run apps/streamlit_app/app.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

ingest:
	python scripts/ingest_knowledge.py

seed:
	python scripts/seed_synthetic_letters.py
