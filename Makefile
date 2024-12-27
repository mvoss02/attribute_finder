run:
	@echo "Running the run script..."
	uv run python run.py

run-with-ingest-data:
	@echo "Running data ingest..."
	cd services && cd data_ingest && make ingest-data

	@echo "Running the run script..."
	uv run python run.py