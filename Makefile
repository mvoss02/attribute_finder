run-dev:
	uv run python run.py

run-with-ingest-data:
	cd services && cd data_ingest && make ingest-data
	uv run python run.py