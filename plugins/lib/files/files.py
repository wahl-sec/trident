#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident Plugin: Filesystem Entries Library
Includes operations like listing entries, metadata for entries, ... 
Implemented using generators to allow for asynchronous plugins.
@author: Jacob Wahlman
"""

from typing import AnyStr, Generator, List, Union, Dict

from os import scandir, DirEntry, stat, stat_result
from re import match


def list_entries(path: AnyStr=None, pattern: AnyStr=None, depth: int=0, exclude: List[AnyStr]=None) -> Generator[DirEntry, None, None]:
    """ Lists all the entries at the specific path.
    Defaults to only scan the current depth (0) of entries.

    :param path: Path to start listing from, defaults to None
    :type path: AnyStr, optional
    :param pattern: Pattern to match entries on in regex form, defaults to None
    :type pattern: AnyStr, optional
    :param depth: Max depth of directories that the scanner will visit, if the depth is -1 then the scanner will traverse until it reaches the end, defaults to 0
    :type depth: int, optional
    :param exclude: Entries to exclude, if the entry is a directory then that entire path will be skipped, defaults to None
    :type exclude: List[AnyStr], optional
    :yield: DirEntry
    :returns: Generator of entries matching the pattern
    :rtype: Generator[DirEntry, None, None]
    """
    def _generator(iterator: Generator, pattern: AnyStr, current_depth: int, exclude: AnyStr):
        try:
            while True:
                _object = next(iterator)
                if exclude is not None and any([match(pattern, _object.name) or match(pattern, _object.path) for pattern in exclude]):
                    continue

                if _object.is_dir() and (current_depth < depth or depth == -1):
                    for _inner in _generator(scandir(_object.path), pattern, current_depth + 1, exclude):
                        yield _inner

                if pattern is None or match(pattern, _object.path):
                    yield _object

        except StopIteration:
            pass

    return _generator(scandir(path), pattern, 0, exclude)

def get_entry(path: AnyStr, symlink: bool=False) -> Union[DirEntry, None]:
    """ Get the entry for a specific path.
    If the entry does not exist at a given path then return None.

    :param path: Path to the entry on the system
    :type path: AnyStr
    :param symlink: If symlinks should be followed if the given path is a symlink, defaults to False
    :type symlink: bool
    :returns: The entry for a given path, None if no entry is found
    :rtype: Union[DirEntry, None]
    """
    pass

def execute(entry: Union[DirEntry, AnyStr], flags: List[AnyStr]=None) -> List[OUTPUT, ERROR]:
    """ Execute a executable entry from a specific path or given entry.

    :param entry: The entry to execute
    :type entry: Union[DirEntry, AnyStr]
    :param flags: Flags to pass to the executable, defaults to None
    :type flags: List[AnyStr], optional
    :return: The `stdout` and `stderr` stream from the executable 
    :rtype: List[OUTPUT, ERROR] TODO: Determine how to return a output,error stream 
    """
    pass

def entry_metadata(entry: Union[DirEntry, AnyStr]) -> stat_result:
    """ Return the metadata of the given entry or path to the entry on the filesystem.

    :raises FileNotFoundError: If the file does not exist for the given path
    :param entry: Entry or path to entry to list metadata for
    :type entry: Union[DirEntry, AnyStr]
    :return: Dictionary of metadata for the given entry
    :rtype: stat_result
    """
    if isinstance(entry, DirEntry):
        return entry.stat()

    return stat(entry)
