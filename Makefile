.PHONY: install dev run test eval docker

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload --port 8000

test:
	USE_MOCK=1 pytest -q

eval:
	python -m evals.run_evals --write

docker:
	docker build -t bharat-doc-intelligence . && \
	docker run -p 8000:8000 --env-file .env bharat-doc-intelligence
