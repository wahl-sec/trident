#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools
from glob import glob

with open("README.md", "r") as README:
    long_description = README.read()


setuptools.setup(
    name="trident",
    version="1.0.0",
    author="Jacob Wahlman",
    description="Trident: Dynamic Resource and Security Monitor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wahl-sec/trident",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operation System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=["psutil>=5.9.0"],
    extras_require={
        "dev": [
            "wheel>=0.35.1",
            "pytest>=6.2.1",
            "sphinx>=4.1.2",
            "furo==2021.7.28b40",
            "black>=21.7b0",
            "grpcio>=1.51.1",
            "grpcio-tools>=1.51.1",
        ]
    },
    zip_safe=False,
)
