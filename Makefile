IMAGE ?= cod-metrics-api:latest

.PHONY: install lint test build run stop clean compose-up compose-down

install:
	pip install -r requirements-dev.txt

lint:
	flake8 src/ tests/

test:
	pytest

build:
	docker build -t $(IMAGE) .

# Lance les tests dans un conteneur (comme le stage Build & Test du pipeline).
test-docker:
	docker run --rm -v "$(CURDIR)":/app -w /app $(IMAGE) \
		sh -c "pip install --no-cache-dir -r requirements-dev.txt && pytest"

run:
	docker run -d --name cod-metrics -p 8001:8000 $(IMAGE)

stop:
	docker rm -f cod-metrics || true

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down -v || true

clean:
	docker rm -f cod-metrics cod-metrics-staging || true
	docker rmi $(IMAGE) || true
