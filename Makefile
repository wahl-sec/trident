SHELL := /usr/bin/env bash

.TRIDENT: install
install:
	pip install setuptools && pip install pybind11
	pip install -e .[dev]

.TRIDENT: install-win
install-win:
	pip install setuptools && pip install pybind11
	pip install -e .[dev]

.TRIDENT: clean
clean:
	python -m pip uninstall -y trident
	find . -name "*.pyc" -exec rm -f {} \;
	rm -rf dist
	rm -rf build
	rm -rf trident.egg-info

.TRIDENT: test
test:
	pip install setuptools && pip install pybind11
	pip install -e .[dev]
	pytest -v

.TRIDENT: build
build:
	pip install setuptools && pip install pybind11
	python setup.py bdist_wheel
