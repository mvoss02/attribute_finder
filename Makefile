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

# Ingest data
load-data:
	@echo "Loading data from API and merging it with attributes..."
	uv run python -m src.data_preprocessing

# Run model response
run-response-model:
	@echo "Running the response model..."
	uv run python run.py

run-response-model-dev:
	@echo "Running the response model in development mode..."
	uv run python -m response

# Visualize output
visualize-output:
	@echo "Visualizing the output..."
	uv run python -m visualize

# Bash script to install local packages
make-install-local-packages-executable:
	chmod +x install_local_packages.sh

install-local-packages: make-install-local-packages-executable
	./install_local_packages.sh