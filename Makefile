IMAGE_TAG=impulsogov/simulacovid

UNAME := $(shell uname)
ifeq ($(UNAME), Linux)
SHELL := /bin/bash
else
SHELL := /bin/sh
endif

###
# Docker
###

# Build image
docker-build:
	docker build -t $(IMAGE_TAG) .

# Run just like the production environment
docker-run:
	docker run -d \
		--name farolcovid \
		--restart=unless-stopped \
		-v $(PWD)/.env:/home/ubuntu/.env:ro \
		-p 8501:8501 \
		-p 5000:5000 \
		$(IMAGE_TAG)

# Run development server with file binding from './src'
start-redis:
	docker run --rm -d --name redis -p 6379:6379 redis:5
destroy-redis:
	docker rm -f redis

# Creates network to access API on localhost (dev)
# TL;DR: your app and API runs on different containers, thus
# localhost:7000 is not the same as your workstation onthis container.
# To run with your local API you need to create a shared network for them.
# See more: https://medium.com/it-dead-inside/docker-containers-and-localhost-cannot-assign-requested-address-6ac7bc0d042b
create-network:
	docker network ls|grep my-network > /dev/null || echo "network does not exist"

docker-dev:
	touch $(PWD)/.env
	docker run --rm -it \
		--net=my-network \
		--name farolcovid \
		-p 8501:8501 \
		-p 5000:5000 \
		-v $(PWD)/.env:/home/ubuntu/.env:ro \
		-v $(PWD)/src:/home/ubuntu/src:ro \
		$(IMAGE_TAG)

# Groups
docker-build-run: docker-build docker-run
docker-build-dev: create-network docker-build docker-dev

# DEBUGING for production environment
docker-shell:
	docker run --rm -it \
		--entrypoint "/bin/bash" \
		-v $(PWD)/.env:/home/ubuntu/.env:ro \
		$(IMAGE_TAG)

# DEBUGING for staging environment
docker-heroku-test: docker-build
	docker run -it --rm \
		-e PORT=8080 \
		-p 8080:8080 \
		-p 5000:5000 \
		$(IMAGE_TAG)
