run-dev:
	uv run python run.py

run-with-ingest-data:
	cd services && make ingest-data
	uv run python run.py