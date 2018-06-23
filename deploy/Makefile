all:
	@echo Prepares CI docker image

1-build:
	docker build -t ubuntu-xenial-rflow .

2-test:
	docker run ubuntu-xenial-rflow

3-tag:
	docker tag ubuntu-xenial-rflow otaviog/ubuntu-xenial-rflow

4-push:
	docker push otaviog/ubuntu-xenial-rflow

