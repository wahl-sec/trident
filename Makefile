SHELL := /usr/bin/env bash

.TRIDENT: install
install:
	python3 -m pip install setuptools && python3 -m pip install pybind11 && python3 -m pip install setuptools_rust
	python3 -m pip install -e .[dev]

.TRIDENT: install-win
install-win:
	python3 -m pip install setuptools && python3 -m pip install pybind11 && python3 -m pip install setuptools_rust
	python3 -m pip install -e .[dev]

.TRIDENT: clean
clean:
	python3 -m pip uninstall -y trident
	find . -name "*.pyc" -exec rm -f {} \;
	rm -rf dist
	rm -rf build
	rm -rf trident.egg-info

.TRIDENT: test
test:
	python3 -m pip install setuptools && python3 -m pip install pybind11 && python3 -m pip install setuptools_rust
	python3 -m pip install -e .[dev]
	pytest -v

.TRIDENT: build
build:
	python3 -m pip install setuptools && python3 -m pip install pybind11 && python3 -m pip install setuptools_rust
	python3 setup.py bdist_wheel
