lint:
	isort -rc .
_tests:
	flake8
	mypy --no-strict-optional pulsar/ # --html-report .mypy-html pulsar/
	pytest --cov-report term-missing --cov-branch --cov=pulsar tests/
_docs:
	find docs/ -type f -name "*.rst" -exec touch "{}" \;
	sphinx-build -M html docs ../pulsar-docs
tests: _tests
docs: _docs
