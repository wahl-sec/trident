#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

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
            "wheel>=0.38.4",
            "pytest>=7.2.1",
            "sphinx>=6.1.3",
            "furo==2022.12.7",
            "black>=23.1.0",
            "mypy>=1.0.0"
        ]
    },
    zip_safe=False,
)
