#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools
from glob import glob
from pybind11.setup_helpers import Pybind11Extension, build_ext

with open("README.md", "r") as README:
    long_description = README.read()

ext_modules = [
	Pybind11Extension(
		"plugins.lib.files.files_",
		list(glob("plugins/lib/files/files.cpp"))
	)
]

setuptools.setup(
    name="trident",
    version="1.0.0",
    author="Jacob Wahlman",
    description="Trident: Dynamic Resource and Security Monitor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/wahl-sec/trident",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operation System :: OS Independent"
    ],
    python_requires=">=3.7",
	extras_require={
		"dev": ["wheel>=0.35.1", "pytest>=6.2.1", "pybind11>=2.6.2", "sphinx>=3.4.3", "sphinx-rtd-theme>=0.5.1"]
	},
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False
)
