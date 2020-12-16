SHELL := /usr/bin/env bash

.TRIDENT: install
install:
	python setup.py install

.TRIDENT: install external
install external:
	pip install -r dev-requirements.txt
	pip install -r requirements.txt
	python setup.py install

.TRIDENT: clean
clean:
	python -m pip uninstall -y trident
	find . -name "*.pyc" -exec rm -f {} \;
	rm -rf dist
	rm -rf build
	rm -rf trident.egg-info

.TRIDENT: test
test:
	python setup.py install
	pip install pytest
	pytest
