SENTRY_PATH := `python -c 'import sentry; print sentry.__file__.rsplit("/", 3)[0]'`

develop: setup-git
	pip install "pip>=7"
	pip install -e .
	npm install

install-tests: develop
	pip install .[tests]

setup-git:
	git config branch.autosetuprebase always
	cd .git/hooks && ln -sf ../../hooks/* ./

lint: lint-js lint-python

lint-python:
	@echo "--> Linting python"
	${SENTRY_PATH}/bin/lint --python .
	@echo ""

lint-js:
	@echo "--> Linting javascript"
	${SENTRY_PATH}/bin/lint --js static/getsentry/
	@echo ""

test: install-tests
	py.test

.PHONY: develop install-tests
