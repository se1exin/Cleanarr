IMG_NAME?=cleanarr
HOST_PORT?=8080
CONTAINER_PORT?=80
CONFIG_MOUNT?=

.env:
	@if [ ! -f .env ]; then cp .env.template .env; fi

.PHONY: build
build: .env
	@docker build -t=$(IMG_NAME) .

.PHONY: run
run:
	@opts=""; if [ "$(CONFIG_MOUNT)" != "" ]; then opts="$$opts -v $(CONFIG_MOUNT):/config"; fi; \
	docker run --rm --env-file=.env -p $(HOST_PORT):$(CONTAINER_PORT) $$opts -ti $(IMG_NAME)

.PHONY: benchmark_backend
benchmark_backend:
	@cd backend && PYTHONPATH=$$(pwd) pytest -v benchmarks.py
