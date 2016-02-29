develop:
	pip install "pip>=7"
	pip install -e .

install-tests: develop
	pip install .[tests]

.PHONY: develop install-tests
