run-dev:
	@echo "Running several examples through the LLM..."
	uv run python get_attribute.py

run:
	@echo "Obtaining the attribute responses from the LLM..."
	uv run python run.py

run-with-ingest-data:
	@echo "Running data ingest..."
	cd .. && cd data_ingest && make ingest-data

	@echo "Running the run script..."
	uv run python run.py

run-dev-img:
	@echo "Testing the image conversion..."
	uv run python image_preprocessing.py
	