.PHONY: all build clean test

# TAG for Docker image version  (defaults to latest)
TAG ?= latest

# Build Docker image (locally, for debugging)
build-for-dev:
	docker build -f Dockerfile -t attribute-finder:$(TAG) .

# Build Docker image (for container registry, production)
build-for-cr:
	docker buildx build --platform linux/amd64 -f Dockerfile -t pimservicecontainerregistry-cfbkatewhxevapaf.azurecr.io/samples/attribute-finder:$(TAG) .

push-to-cr:
	docker push pimservicecontainerregistry-cfbkatewhxevapaf.azurecr.io/samples/attribute-finder:$(TAG)

# Run container with mounted data
run-with-docker: build-for-dev
	docker run -it \
		-v $$(pwd)/data:/app/data \
		attribute-finder:$(TAG)

# Clean up Docker resources
clean:
	docker rmi attribute-finder

# Ingest data
load-data:
	@echo "Loading data from API and merging it with attributes..."
	uv run python -m src.data_preprocessing

# Run model response
run-response-model:
	@echo "Running the response model..."
	uv run python run.py

# Visualize output - currentlyt not working...
visualize-output:
	@echo "Visualizing the output..."
	uv run python -m visualize

