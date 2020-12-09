all:
	@echo Prepares CI docker image

1-build:
	docker build -t otaviog/ubuntu-rflow-ci .

2-shell:
	docker run -it otaviog/ubuntu-rflow-ci /bin/bash

3-tag:
	docker tag otaviog/ubuntu-rflow-ci otaviog/ubuntu-rflow-ci:latest

4-push:
	docker push otaviog/ubuntu-rflow-ci:latest
