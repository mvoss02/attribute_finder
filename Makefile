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