.PHONY: build run-with-docker clean

# Build Docker image
build:
	docker build -f Dockerfile -t attribute-finder .

# Run container with mounted data
run-with-docker: build
	docker run -it \
		-v $$(pwd)/data:/app/data \
		attribute-finder

# Clean up Docker resources
clean:
	docker rmi attribute-finder

ingest-data:
	@echo "Ingesting the data, in order to create a final dataset..."
	uv run python -m src.data_ingest.data_ingestion

run-response-model:
	@echo "Running the response model..."
	uv run python run.py

visualize-output:
	@echo "Visualizing the output..."
	uv run python -m src.utils.visualize_output