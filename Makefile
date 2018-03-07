SENTRY_PATH := `python -c 'import sentry; print sentry.__file__.rsplit("/", 3)[0]'`
UNAME_S := $(shell uname -s)

develop: setup-git install-yarn
	pip install "pip>=9,<10"
	pip install -e git+https://github.com/getsentry/sentry.git#egg=sentry[dev]
	pip install -e .
	yarn install

install-yarn:
	@echo "--> Installing Node dependencies"
	@hash yarn 2> /dev/null || npm install -g yarn
	# Use NODE_ENV=development so that yarn installs both dependencies + devDependencies
	NODE_ENV=development yarn install --ignore-optional

install-tests: develop install-chromedriver
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

install-chromedriver:
ifeq ($(UNAME_S), Darwin)
	@echo "NOTE: Install chromedriver via Homebrew, with: brew install chromedriver"
else
	wget -N http://chromedriver.storage.googleapis.com/2.33/chromedriver_linux64.zip -P ~/
	unzip ~/chromedriver_linux64.zip -d ~/
	rm ~/chromedriver_linux64.zip
	chmod +x ~/chromedriver
	mkdir -p ~/.bin
	mv ~/chromedriver ~/.bin/
endif

lint: lint-js lint-python

lint-python:
	@echo "--> Linting python"
	bash -eo pipefail -c "${SENTRY_PATH}/bin/lint --python --parseable . | tee flake8.pycodestyle.log"
	@echo ""

lint-js:
	@echo "--> Linting javascript"
	bash -eo pipefail -c "${SENTRY_PATH}/bin/lint --js --parseable . | tee eslint.codestyle.xml"
	@echo ""

test: install-tests
	py.test

.PHONY: develop install-tests
