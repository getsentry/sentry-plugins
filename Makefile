SENTRY_PATH := `python -c 'import sentry; print sentry.__file__.rsplit("/", 3)[0]'`
PIP := python -m pip
PIP_VERSION := 19.2.3
PIP_OPTS := --no-use-pep517 --disable-pip-version-check

develop: install-develop-requirements

install-pip:
	$(PIP) install "pip==$(PIP_VERSION)"

setup-git:
	@echo "--> Installing git hooks"
	git config branch.autosetuprebase always
	git config core.ignorecase false
	cd .git/hooks && ln -sf ../../config/hooks/* ./
	$(PIP) install $(PIP_OPTS) "pre-commit==1.18.2"
	pre-commit install --install-hooks
	@echo ""

install-yarn:
	@echo "--> Installing Node dependencies"
	@hash yarn 2> /dev/null || npm install -g yarn

install-requirements: install-pip install-yarn
	yarn install
	$(PIP) install $(PIP_OPTS) 'git+https://github.com/getsentry/sentry.git#egg=sentry'
	$(PIP) install $(PIP_OPTS) .

install-develop-requirements: setup-git install-pip install-yarn
	NODE_ENV=development yarn install --ignore-optional
	$(PIP) install $(PIP_OPTS) -e "../sentry[dev]"
	$(PIP) install $(PIP_OPTS) -e ".[tests]"

# this is for ci, so no relative sentry
# XXX: sentry and itself is installed editable to prevent wheel building for now until i figure out why it fails
install-tests: install-pip install-yarn
	NODE_ENV=development yarn install --ignore-optional
	$(PIP) install $(PIP_OPTS) -e 'git+https://github.com/getsentry/sentry.git#egg=sentry'
	$(PIP) install $(PIP_OPTS) -e ".[tests]"

clean:
	@echo "--> Cleaning static cache"
	rm -f src/sentry_plugins/*/static/dist
	@echo "--> Cleaning pyc files"
	find . -name "*.pyc" -delete
	@echo "--> Cleaning python build artifacts"
	rm -rf build/ dist/ src/sentry_plugins/assets.json
	@echo ""

lint: lint-js lint-python

lint-python:
	@echo "--> Linting python"
	bash -eo pipefail -c "flake8 | tee .artifacts/flake8.pycodestyle.log"
	@echo ""

lint-js:
	@echo "--> Linting javascript"
	bash -eo pipefail -c "${SENTRY_PATH}/bin/lint --js --parseable . | tee .artifacts/eslint.codestyle.xml"
	@echo ""

.PHONY: develop install-pip setup-git install-yarn install-requirements install-develop-requirements install-tests clean lint lint-python lint-js
