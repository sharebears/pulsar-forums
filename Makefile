lint:
	isort -rc .

tests:
	flake8
	mypy --no-strict-optional forums/
	pytest --cov-report term-missing --cov-branch --cov=forums tests/

.PHONY: lint tests
