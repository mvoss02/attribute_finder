.PHONY: all build clean test

# TAG for Docker image version  (defaults to latest)
TAG ?= latest

# Build Docker image (locally, for debugging)
build-for-dev:
	docker build -f Dockerfile -t attribute-finder:$(TAG) .

# Build Docker image (for container registry, production)
build-for-cr:
	docker buildx build --platform linux/amd64 -f Dockerfile -t pimservicecontainerregistry-cfbkatewhxevapaf.azurecr.io/pim/attribute-finder:$(TAG) .

push-to-cr:
	docker push pimservicecontainerregistry-cfbkatewhxevapaf.azurecr.io/pim/attribute-finder:$(TAG)

# Run container with mounted data and not with API!
run-with-docker-dev: build-for-dev
	docker run -it \
		-v $$(pwd)/data:/app/data \
		attribute-finder:$(TAG)

# Run container with mounted data and with API!
run-with-docker-dev-api: build-for-dev
	docker run -it -p 8000:8000 \
		-v $$(pwd)/data:/app/data \
		attribute-finder:$(TAG)

# Clean up Docker resources
clean:
	docker rmi attribute-finder:$(TAG)

# Run model response
run-response-model:
	@echo "Running the response model..."
	uv run python run.py

# Run API
run-api:
	@echo "Running the API..."
	uv run uvicorn src.api:app --host 0.0.0.0 --port 80
