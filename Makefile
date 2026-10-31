.PHONY: up down logs test seed
up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

test:
	pytest

seed:
	python scripts/seed_demo.py
