#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident Plugin: Filesystem Library
Includes operations like filesystem format, disk usage, ...
Implemented using generators to allow for asynchronous plugins.
@author: Jacob Wahlman
"""

from typing import Optional, Union, Generator

from dataclasses import dataclass
from shutil import disk_usage
from pathlib import Path

from psutil import disk_partitions


@dataclass
class Filesystem:
    """Represents metadata structure for a filesystem.
    Instances of the class is stored inside the entry instances.
    The class is JSON serializable in order to be easily
    represented in the data stores.
    """

    path: str
    mountpoint: Optional[str]
    fstype: str
    max_size: float
    current_size: float
    free_size: float


def filesystem(path: str) -> Union[Filesystem, None]:
    """Return the filesystem representation for a given path.

    :param path: The path on the system for the filesystem
    :type path: str
    :returns: The filesystem object for the path
    :rtype: Union[Filesystem, None]
    """
    path_ = Path(path)
    path_prefix = path_.drive if path_.drive else path_.root

    return Filesystem(
        path=path_prefix,
        format=None,
        max_size=file_path_total(path_prefix),
        current_size=file_path_usage(path_prefix),
        free_size=file_path_usage(path_prefix),
    )


def file_path_usage(path: str) -> Union[float, None]:
    """Return the disk usage of the given path.

    :param path: The path can be either a file or directory
    :type path: str
    :returns: The disk usage for the given path
    :rtype: Union[float, None]
    """
    usage = disk_usage(path)
    return usage[1] if isinstance(usage, tuple) else None


def file_path_total(path: str) -> Union[float, None]:
    """Return the total disk space of the given path.

    :param path: The path can be either a file or directory
    :type path: str
    :returns: The total disk space for the given path
    :rtype: Union[float, None]
    """
    usage = disk_usage(path)
    return usage[0] if isinstance(usage, tuple) else None


def file_path_free(path: str) -> Union[float, None]:
    """Return the free disk space of the given path.

    :param path: The path can be either a file or directory
    :type path: str
    :returns: The free disk space for the given path
    :rtype: Union[float, None]
    """
    usage = disk_usage(path)
    return usage[2] if isinstance(usage, tuple) else None


def file_disk_partitions() -> Generator[Filesystem, None, None]:
    """Return generator yielding filesystem descriptiors identified on the system.

    :returns: Generator of filesystems descriptors
    :rtype: Generator[Filesystem, None, None]
    """
    for part in disk_partitions(all=True):
        try:
            yield Filesystem(
                path=part.device,
                mountpoint=part.mountpoint,
                fstype=part.fstype,
                max_size=file_path_total(path=part.device),
                current_size=file_path_usage(path=part.device),
                free_size=file_path_free(path=part.device),
            )
        except FileNotFoundError:
            yield Filesystem(
                path=part.device,
                mountpoint=part.mountpoint,
                fstype=part.fstype,
                max_size=file_path_total(path=part.mountpoint),
                current_size=file_path_usage(path=part.mountpoint),
                free_size=file_path_free(path=part.mountpoint),
            )
        else:
            yield Filesystem(
                path=part.device,
                mountpoint=part.mountpoint,
                fstype=part.fstype,
                max_size=None,
                current_size=None,
                free_size=None,
            )
