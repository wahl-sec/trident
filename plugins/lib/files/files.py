#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident Plugin: Filesystem Entries Library
Includes operations like listing entries (files, directories, ...), metadata for entries, ...
Implemented using generators to allow for asynchronous plugins.
@author: Jacob Wahlman
"""

from typing import AnyStr, Generator, List, Union, Dict, TextIO, Tuple, NoReturn

from os import scandir, DirEntry, stat, remove, rmdir
from subprocess import Popen, PIPE
from pathlib import Path


class EntryStat(dict):
    """Represents metadata structure for an entry.
    Instances of the class is stored inside the entry instances.
    The class is JSON serializable in order to be easily
    represented in the data stores.
    """

    mode: int
    inode: int
    device: int
    nlinks: int
    uid: int
    gid: int
    size: int
    atime: float
    mtime: float
    ctime: float

    def __init__(
        self, mode, inode, device, nlinks, uid, gid, size, atime, mtime, ctime
    ):
        dict.__init__(
            self,
            mode=mode,
            inode=inode,
            device=device,
            nlinks=nlinks,
            uid=uid,
            gid=gid,
            size=size,
            atime=atime,
            mtime=mtime,
            ctime=ctime,
        )


class Entry(dict):
    """Represents an entry (files, directories, ...).
    The class is JSON serializable in order to be easily
    represented in the data stores.
    """

    path: str
    name: str
    stat: EntryStat

    def __init__(self, path, name, stat):
        dict.__init__(self, path=path, name=name, stat=stat)


def entries(
    path: AnyStr,
    patterns: List[AnyStr] = None,
    depth: int = 0,
    exclude: List[AnyStr] = None,
) -> Generator[DirEntry, None, None]:
    """Lists all the entries at the specific path.
    Defaults to only scan the current depth (0) of entries.

    :param path: Path to start listing from
    :type path: AnyStr
    :param patterns: List of patterns to match entries on in regex form, defaults to None
    :type patterns: List[AnyStr], optional
    :param depth: Max depth of directories that the scanner will visit, if the depth is -1 then the scanner will traverse until it reaches the end, defaults to 0
    :type depth: int, optional
    :param exclude: Entries to exclude, if the entry is a directory then that entire path will be skipped, defaults to None
    :type exclude: List[AnyStr], optional
    :yield: DirEntry
    :returns: Generator of entries matching the pattern
    :rtype: Generator[DirEntry, None, None]
    """

    def _generator(
        iterator: Generator,
        patterns: List[AnyStr],
        current_depth: int,
        exclude: List[AnyStr],
    ):
        try:
            while True:
                _object = next(iterator)
                if exclude is not None and any(
                    [
                        Path(_object.name).match(pattern)
                        or Path(_object.path).match(pattern)
                        for pattern in exclude
                    ]
                ):
                    continue

                if _object.is_dir() and (current_depth < depth or depth == -1):
                    for _inner in _generator(
                        scandir(_object.path), patterns, current_depth + 1, exclude
                    ):
                        yield _inner

                if patterns is None or any(
                    [
                        Path(_object.name).match(pattern)
                        or Path(_object.path).match(pattern)
                        for pattern in patterns
                    ]
                ):
                    yield Entry(
                        path=_object.path,
                        name=_object.name,
                        stat=entry_metadata(_object),
                    )

        except StopIteration:
            pass

    return _generator(scandir(path), patterns, 0, exclude)


def execute(
    entry: Union[DirEntry, AnyStr],
    flags: List[AnyStr] = [],
    stdin: TextIO = PIPE,
    stdout: TextIO = PIPE,
    stderr: TextIO = PIPE,
    wait: bool = False,
) -> Tuple[TextIO, TextIO, TextIO, int]:
    """Execute a executable entry from a specific path or given entry.

    :param entry: The entry to execute
    :type entry: Union[DirEntry, AnyStr]
    :param flags: Flags to pass to the executable, defaults to None
    :type flags: List[AnyStr], optional
    :return: The `stdin`, `stdout` and `stderr` stream from the executable and the return code
    :rtype: List[TextIO, TextIO, TextIO, int]
    """
    proc = Popen([entry] + flags, stdin=stdin, stdout=stdout, stderr=stderr)
    while wait and proc.poll() is None:
        pass

    return [proc.stdin, proc.stdout, proc.stderr, proc.returncode]


def entry_metadata(entry: Union[DirEntry, AnyStr]) -> EntryStat:
    """Return the metadata of the given entry or path to the entry on the filesystem.

    :raises FileNotFoundError: If the file does not exist for the given path
    :param entry: Entry or path to entry to list metadata for
    :type entry: Union[DirEntry, AnyStr]
    :return: Dictionary of metadata for the given entry
    :rtype: EntryStat
    """
    stat_ = entry.stat() if isinstance(entry, DirEntry) else stat(entry)
    return EntryStat(
        mode=stat_.st_mode,
        inode=stat_.st_ino,
        device=stat_.st_dev,
        nlinks=stat_.st_nlink,
        uid=stat_.st_uid,
        gid=stat_.st_gid,
        size=stat_.st_size,
        atime=stat_.st_atime,
        mtime=stat_.st_mtime,
        ctime=stat_.st_ctime,
    )


def remove_entries(
    path: Union[Entry, AnyStr],
    recursive: bool = False,
    patterns: List[AnyStr] = None,
    exclude: List[AnyStr] = None,
) -> NoReturn:
    """Remove an entry from the filesystem.
    If the entry is a directory then the recursive flag need to be set.

    :param path: Path to start removing from, can also be the specific entry to remove
    :type path: Union[Entry, AnyStr]
    :param recursive: Remove recursively if the entry is a directory,
    if the entry is of any other type then this flag is ignored
    :type recursive: bool
    :param patterns: List of patterns to match entries on in regex form, defaults to None
    :type patterns: List[AnyStr], optional
    :param exclude: List of patterns to match entries to exclude in regex form,
    defaults to None
    :type exclude: List[AnyStr], optional
    """

    def _remove(entry):
        if Path(entry["path"]).is_dir():
            rmdir(entry["path"])
        else:
            remove(entry["path"])

    if isinstance(path, Entry):
        _remove(path)
    else:
        for entry in entries(
            path=path, depth=-1 if recursive else 0, patterns=patterns, exclude=exclude
        ):
            _remove(entry)
