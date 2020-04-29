PROJECT_NAME := exporter

docker:
	DOCKER_BUILDKIT=1 docker build -t $(PROJECT_NAME) .
