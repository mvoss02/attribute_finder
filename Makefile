# Build Docker image
build:
	docker build -f Dockerfile -t attribute-finder .

# Run container with mounted data
run-with-docker: build
	docker run -it \
		-v $(pwd)/data:/app/data \
		-e IS_TEST_RUN=True \
		-e NUMBER_OF_TEST_CASES=10 \
		--env-file settings.env \
		attribute-finder

# Clean up Docker resources
clean:
    docker rm -f $$(docker ps -aq -f name=attribute-finder)
    docker rmi attribute-finder