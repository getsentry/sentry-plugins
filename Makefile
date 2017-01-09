SENTRY_PATH := `python -c 'import sentry; print sentry.__file__.rsplit("/", 3)[0]'`

develop: setup-git install-yarn
	pip install "pip>=7"
	pip install -e git+https://github.com/getsentry/sentry.git#egg=sentry[dev]
	pip install -e .
	yarn install

install-yarn:
	@echo "--> Installing Node dependencies"
	@hash yarn 2> /dev/null || npm install -g yarn
	# Use NODE_ENV=development so that yarn installs both dependencies + devDependencies
	NODE_ENV=development yarn install --ignore-optional

install-tests: develop
	pip install .[tests]

setup-git:
	git config branch.autosetuprebase always
	cd .git/hooks && ln -sf ../../hooks/* ./

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
	${SENTRY_PATH}/bin/lint --python .
	@echo ""

lint-js:
	@echo "--> Linting javascript"
	${SENTRY_PATH}/bin/lint --js static/getsentry/
	@echo ""

test: install-tests
	py.test

.PHONY: develop install-tests
