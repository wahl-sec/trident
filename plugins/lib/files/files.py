#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident Plugin: Files Library
Common file system operations used in Trident plugins.
Implemented using generators to allow for asynchronous plugins.
@author: Jacob Wahlman
"""

from typing import AnyStr, Generator

from os import scandir, DirEntry
from re import match


def list_files_iter(path: AnyStr=None, pattern: AnyStr=None) -> Generator:
    def _generator(iterator: Generator, pattern: AnyStr):
        try:
            while True:
                _object = next(iterator)
                if pattern is None or match(pattern, _object.path):
                    yield _object

        except StopIteration:
            pass

    return _generator(scandir(path), pattern)

def list_files_iter_r(path: AnyStr=None, pattern: AnyStr=None) -> Generator:
    def _generator(iterator: Generator, pattern: AnyStr):
        try:
            while True:
                _object = next(iterator)
                if _object.is_dir():
                    for _inner in _generator(list_files(_object.path), pattern):
                        yield _inner

                if pattern is None or match(pattern, _object.path):
                    yield _object

        except StopIteration:
            pass

    return _generator(scandir(path), pattern)
