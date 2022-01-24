#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident Plugin: Filesystem Entries Library
Includes operations like listing entries (files, directories, ...), metadata for entries, ...
Implemented using generators to allow for asynchronous plugins.
@author: Jacob Wahlman
"""

from typing import (
    AnyStr,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Union,
    TextIO,
    Tuple,
    NoReturn,
)

from os import DirEntry, scandir, stat, remove, rmdir
from os.path import commonpath
from subprocess import Popen, PIPE
from dataclasses import dataclass
from pathlib import Path
from re import compile
import zipfile
import tarfile


@dataclass
class EntryStat:
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


@dataclass
class Entry:
    """Represents an entry (files, directories, ...).
    The class is JSON serializable in order to be easily
    represented in the data stores.
    """

    path: str
    name: str
    stat: EntryStat


def entries(
    path: str,
    patterns: List[str] = None,
    depth: int = 0,
    exclude: List[str] = None,
    follow_symlinks: bool = True,
    exceptions: bool = False,
) -> Generator[DirEntry, None, None]:
    """Lists all the entries at the specific path.
    Defaults to only scan the current depth (0) of entries.

    :param path: Path to start listing from
    :type path: str
    :param patterns: List of patterns to match entries on in regex form, defaults to None
    :type patterns: List[str], optional
    :param depth: Max depth of directories that the scanner will visit, if the depth is -1 then the scanner will traverse until it reaches the end, defaults to 0
    :type depth: int, optional
    :param exclude: Entries to exclude, if the entry is a directory then that entire path will be skipped, defaults to None
    :type exclude: List[str], optional
    :param exceptions: Raise exceptions that occur to the plugin for it to handle, if set to `False` no exceptions will be raised, defaults to `False`
    :type exceptions: bool, optional
    :yield: DirEntry
    :returns: Generator of entries matching the pattern
    :rtype: Generator[DirEntry, None, None]
    """

    def _generator(
        iterator: Generator,
        patterns: List[str],
        current_depth: int,
        exclude: List[str],
        follow_symlinks: bool,
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

                if (
                    _object.is_dir()
                    and (current_depth < depth or depth == -1)
                    and (
                        (_object.is_symlink() and follow_symlinks)
                        or not _object.is_symlink()
                    )
                ):
                    try:
                        for _inner in _generator(
                            scandir(_object.path),
                            patterns,
                            current_depth + 1,
                            exclude,
                            follow_symlinks,
                        ):
                            yield _inner
                    except Exception as exc:
                        if exceptions:
                            raise exc from None
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

    return _generator(scandir(path), patterns, 0, exclude, follow_symlinks)


def execute(
    entry: Union[DirEntry, str],
    flags: List[str] = [],
    stdin: TextIO = PIPE,
    stdout: TextIO = PIPE,
    stderr: TextIO = PIPE,
    wait: bool = False,
    pre: List[str] = [],
    post: List[str] = [],
    exceptions: bool = True,
) -> Tuple[TextIO, TextIO, TextIO, int]:
    """Execute a executable entry from a specific path or given entry.

    :param entry: The entry to execute
    :type entry: Union[DirEntry, str]
    :param flags: Flags to pass to the executable, defaults to None
    :type flags: List[str], optional
    :param wait: If the program should wait for the execution to finish or continue running, defaults to `False`
    :type wait: bool, optional
    :param pre: The command(s) to add before the entry, can be used to chain commands for example `["cat"]`
    :type pre: List[str], optional
    :param post: The command(s) to add after the entry, can be used to chain commands for example `["|", "grep", "abc"]`
    :type post: List[str], optional
    :param exceptions: Raise exceptions that occur to the plugin for it to handle, if set to `False` no exceptions will be raised, defaults to `True`
    :type exceptions: bool, optional
    :return: The `stdin`, `stdout` and `stderr` stream from the executable and the return code
    :rtype: List[TextIO, TextIO, TextIO, int]
    """
    _path = entry.path if isinstance(entry, Entry) else entry
    try:
        proc = Popen(
            pre + [_path] + flags + post, stdin=stdin, stdout=stdout, stderr=stderr
        )
    except Exception as exc:
        if exceptions:
            raise exc from None

    while wait and proc.poll() is None:
        pass

    return [proc.stdin, proc.stdout, proc.stderr, proc.returncode]


def entry_metadata(entry: Union[DirEntry, str], exceptions: bool = True) -> EntryStat:
    """Return the metadata of the given entry or path to the entry on the filesystem.

    :raises FileNotFoundError: If the file does not exist for the given path
    :param entry: Entry or path to entry to list metadata for
    :type entry: Union[DirEntry, str]
    :param exceptions: Raise exceptions that occur to the plugin for it to handle, if set to `False` no exceptions will be raised, defaults to `True`
    :type exceptions: bool, optional
    :return: Dictionary of metadata for the given entry
    :rtype: EntryStat
    """
    try:
        stat_ = entry.stat() if isinstance(entry, DirEntry) else stat(entry)
    except Exception as exc:
        if exceptions:
            raise exc from None

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


def remove_entry(
    path: Union[Entry, str],
    recursive: bool = False,
    patterns: List[str] = None,
    exclude: List[str] = None,
    exceptions: bool = True,
) -> NoReturn:
    """Remove an entry from the filesystem.
    If the entry is a directory then the recursive flag need to be set.

    :param path: Path to start removing from, can also be the specific entry to remove
    :type path: Union[Entry, str]
    :param recursive: Remove recursively if the entry is a directory,
    if the entry is of any other type then this flag is ignored
    :type recursive: bool
    :param patterns: List of patterns to match entries on in regex form, defaults to None
    :type patterns: List[str], optional
    :param exclude: List of patterns to match entries to exclude in regex form,
    defaults to None
    :type exclude: List[str], optional
    :param exceptions: Raise exceptions that occur to the plugin for it to handle, if set to `False` no exceptions will be raised, defaults to `True`
    :type exceptions: bool, optional
    """

    def _remove(entry):
        if Path(entry["path"]).is_dir():
            rmdir(entry["path"])
        else:
            remove(entry["path"])

    try:
        if isinstance(path, Entry):
            _remove(path)
        else:
            for entry in entries(
                path=path,
                depth=-1 if recursive else 0,
                patterns=patterns,
                exclude=exclude,
            ):
                _remove(entry)
    except Exception as exc:
        if exceptions:
            raise exc from None


def move_entry() -> NoReturn:
    """Move a given entry to another path on the filesystem."""
    pass


def copy_entry() -> NoReturn:
    """Copy the given entry to another path on the filesystem."""
    pass


def update_entry_mode() -> NoReturn:
    """Update the mode for the given entry."""
    pass


def write_entry(
    path: Union[Entry, str],
    content: AnyStr,
    directory: bool = False,
    mode: Literal["w", "a", "w+", "a+", "wb", "ab", "wb+", "ab+"] = "w+",
    entry_mode: int = None,
    overwrite: bool = False,
    parents: bool = False,
    encoding: str = "utf-8",
    exceptions: bool = True,
) -> NoReturn:
    """Write an entry to the filesystem, the entry can be a file or a directory.

    :param path: Path to entry to write to, will create the entry if it doesn't exist or overwrite depending on mode
    :type path: Union[Entry, str]
    :param content: The content to write to the entry, will be ignored if the `directory` parameter is set
    :type content: AnyStr
    :param directory: If the entry to be created is a folder
    :type directory: bool, optional
    :param mode: The mode to use for opening the entry to write
    :type mode: Literal["w", "a", "w+", "a+", "wb", "ab", "wb+", "ab+"], optional
    :param entry_mode: The posix mode permissions to use for creating the entry, defaults to 438
    :type entry_mode: int, optional
    :param overwrite: If an existing entry at the path should be overwritten, defaults to `False`
    :type overwrite: bool, optional
    :param parents: If the parent directories should be created as well if they don't exist, defaults to `False`
    :type parents: bool, optional
    :param encoding: The encoding to use when creating the entry, defaults to UTF-8
    :type encoding: str, optional
    :param exceptions: Raise exceptions that occur to the plugin for it to handle, if set to `False` no exceptions will be raised, defaults to `True`
    :type exceptions: bool, optional
    """
    _path = path.path if isinstance(path, Entry) else path
    try:
        if not directory:
            _entry = Path(_path)
            _entry.touch(
                mode=entry_mode if entry_mode is not None else 438, exist_ok=overwrite
            )
            with _entry.open(mode=mode, encoding=encoding) as entry:
                if not entry.writable():
                    raise OSError(f"Entry at {_path} is not writable.")

                entry.write(content)
        else:
            _entry = Path(_path)
            _entry.mkdir(
                mode=entry_mode if entry_mode is not None else 511,
                parents=parents,
                exist_ok=overwrite,
            )
    except Exception as exc:
        if exceptions:
            raise exc from None


def archive_entry(
    path: List[Union[Entry, str]],
    archive: Union[Entry, str],
    format: Literal["gz", "bz2", "xz", "zip", "tar"] = "zip",
    level: Optional[int] = None,
    preserve_path: bool = False,
    exceptions: bool = True,
):
    """Archive an entry using a given format.

    :param path: Paths to the entries to create an archive from
    :type path: List[Union[Entry, str]]
    :param archive: Path to where the archive should be created
    :type archive: Union[Entry, str]
    :param format: The format to use for the archive, defaults to plain `"zip"`
    :type format: Literal["gz", "bz2", "xz", "zip", "tar"]
    :param level: The compression level to use for the given format, the compression levels are passed as one for each layer of formats, defaults to the default compression level for the format
    :type level: List[int], optional
    :param preserve_path: If the archive should preserve the absolute path to the entry when archiving, default `False`
    :type preserve_path: bool, optional
    :param exceptions: Raise exceptions that occur to the plugin for it to handle, if set to `False` no exceptions will be raised, defaults to `True`
    :type exceptions: bool, optional
    """
    _archive = Path(archive.path) if isinstance(archive, Entry) else Path(archive)
    try:
        if format in ["gz", "bz2", "xz", "tar"]:
            _mode = "w" if format == "tar" else f"w:{format}"
            with tarfile.open(
                name=str(_archive),
                mode=_mode,
                **{"compresslevel": level} if format in ["gz", "bz2", "xz"] else {},
            ) as _tar:
                for _path in path:
                    _path = (
                        Path(_path.path) if isinstance(_path, Entry) else Path(_path)
                    )
                    _tar.add(
                        name=str(_path),
                        recursive=_path.is_dir(),
                        arcname=str(_path).replace(
                            commonpath([str(_archive), str(_path)]), ""
                        )
                        if not preserve_path
                        else None,
                    )
        elif format == "zip":
            with zipfile.ZipFile(
                file=str(_archive),
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=level,
            ) as _zip:
                for _path in path:
                    _path = (
                        Path(_path.path) if isinstance(_path, Entry) else Path(_path)
                    )
                    if _path.is_dir():
                        for _entry in _path.rglob("*"):
                            _zip.write(
                                _entry,
                                arcname=str(_entry).replace(
                                    commonpath([str(_archive), str(_entry)]), ""
                                )
                                if not preserve_path
                                else None,
                            )
                    else:
                        _zip.write(
                            _path,
                            arcname=str(_path).replace(
                                commonpath([str(_archive), str(_path)]), ""
                            )
                            if not preserve_path
                            else None,
                        )
    except Exception as exc:
        if exceptions:
            raise exc from None


def unarchive_entry(
    archive: Union[Entry, str],
    path: Union[Entry, str],
    patterns: List[str] = [],
    excludes: List[str] = [],
    format: Literal["gz", "bz2", "xz", "zip", "tar"] = None,
    password: Optional[str] = None,
    exceptions: bool = True,
):
    """Unarchive an entry using with the given format.

    :param archive: Path to where the archive is to unarchive from
    :type archive: Union[Entry, str]
    :param path: Path to the entry to unarchive the entry to
    :type path: Union[Entry, str]
    :param patterns: Patterns of the members of the archive to extract, defaults to extract all members (`None`)
    :type patterns: Optional[List[str]]
    :param excludes: Patterns of the members of the archive to exclude from being extracted, defaults to no exclusion (`None`)
    :type excludes: Optional[List[str]]
    :param format: The format to use for the unarchive, if not given the format will be detected
    :type format: Literal["gz", "bz2", "xz", "zip", "tar"]
    :param password: Uses the password if given to uncompress the archive
    :type password: Optional[str], optional
    :param exceptions: Raise exceptions that occur to the plugin for it to handle, if set to `False` no exceptions will be raised, defaults to `True`
    :type exceptions: bool, optional
    """
    _archive = Path(archive.path) if isinstance(archive, Entry) else Path(archive)
    _path = Path(path.path) if isinstance(path, Entry) else Path(path)

    def _archive_members(
        _archive_info: Union[tarfile.TarFile, zipfile.ZipFile],
        _patterns: List[str],
        _excludes: List[str],
    ) -> Generator[Union[tarfile.TarInfo, zipfile.ZipInfo], None, None]:
        """Yields the members of the archive matching the patterns provided.

        :param _archive_info: The archive context to fetch members from
        :type _archive_info: Union[tarfile.TarFile, zipfile.ZipFile]
        :param _patterns: Patterns of the members of the archive to extract
        :type _patterns: List[str]
        :param _excludes: Patterns of the members of the archive to extract
        :type _excludes: List[str]
        :return: Generator for the archive members identified by the patterns
        :rtype: Generator[Union[tarfile.TarInfo, zipfile.ZipInfo], None, None]
        """
        for _member in _archive_info:
            for _exclude in _excludes:
                if Path(
                    getattr(
                        _member,
                        "name" if isinstance(_member, tarfile.TarInfo) else "filename",
                    )
                ).match(_exclude):
                    break
            else:
                for _pattern in _patterns:
                    if Path(
                        getattr(
                            _member,
                            "name"
                            if isinstance(_member, tarfile.TarInfo)
                            else "filename",
                        )
                    ).match(_pattern):
                        yield _member

    try:
        if _archive.exists() and (
            format is not None
            or any(
                _archive.suffix == f".{_format}"
                for _format in ["gz", "bz2", "xz", "zip", "tar"]
            )
        ):
            format = (
                format if format is not None else str(_archive.suffix).replace(".", "")
            )
            if format in ["gz", "bz2", "xz", "tar"]:
                _mode = "r" if format == "tar" else f"r:{format}"
                with tarfile.open(name=str(_archive), mode=_mode) as _tar:
                    _tar.extractall(
                        path=str(_path),
                        members=_archive_members(_tar, patterns, excludes)
                        if (patterns or excludes)
                        else None,
                    )
            elif format == "zip":
                with zipfile.ZipFile(file=str(_archive), mode="r") as _zip:
                    if password is not None:
                        _zip.setpassword(password.encode("utf-8"))

                    _zip.extractall(
                        path=str(_path),
                        members=_archive_members(_zip.filelist, patterns, excludes)
                        if (patterns or excludes)
                        else None,
                    )
    except Exception as exc:
        if exceptions:
            raise exc from None


def entry_content_contains(
    path: Union[Entry, str],
    patterns: List[str],
    mode: Literal[
        "r", "w", "a", "r+", "w+", "a+", "rb", "wb", "ab", "rb+", "wb+", "ab+"
    ] = "r",
    encoding: str = "utf-8",
    exceptions: bool = True,
    limit_line: int = -1,
) -> Dict[int, Dict[str, str]]:
    """Return a context used to read and interact with the given entry.
    By default the entry is opened in read-only mode.

    :param path: Path to entry to read from can either be read as text or as binary
    :type path: Union[Entry, str]
    :param patterns: List of patterns to match entries on in regex form
    :type patterns: List[str]
    :param mode: The mode in which to create the context from, defaults to read-only, can be any of the default Python file modes
    :type mode: Literal["r", "w", "a", "r+", "w+", "a+", "rb", "wb", "ab", "rb+", "wb+", "ab+"], optional
    :param encoding: The encoding to use when opening the file, defaults to UTF-8
    :type encoding: str, optional
    :param exceptions: Raise exceptions that occur to the plugin for it to handle, if set to `False` no exceptions will be raised, defaults to `True`
    :type exceptions: bool, optional
    :param limit_line: Limit the line to include to make the logs a bit smaller, defined by number of characters to include, defaults to full line (`-1`)
    :type limit_line: int, optional
    :return: The IO wrapper for the entry
    :rtype: Union[TextIO, BinaryIO]
    """
    _path = path.path if isinstance(path, Entry) else path
    _results = {}
    try:
        with open(_path, mode=mode, encoding=encoding) as entry:
            for index, entry_line in enumerate(entry.readlines()):
                for pattern in patterns:
                    if compile(pattern).match(entry_line):
                        if (index + 1) not in _results:
                            _results[index + 1] = []

                        _results[index + 1].append(
                            {
                                "pattern": pattern,
                                "line": entry_line[:limit_line],
                                "file": _path,
                            }
                        )
    except Exception as exc:
        if exceptions:
            raise exc from None

    return _results
