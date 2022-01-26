#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import AnyStr, List, Optional
from plugins.lib.files.files import (
    archive_entry,
    copy_entry,
    entries,
    entry,
    entry_content_contains,
    execute,
    move_entry,
    remove_entry,
    unarchive_entry,
    update_entry_mode,
    write_entry,
)


class FindFiles:
    def execute_plugin(self, path, patterns: Optional[List[str]] = None):
        for entry in entries(path, patterns=patterns):
            yield entry


class FindFile:
    def execute_plugin(self, path):
        return entry(path=path)


class CopyFiles:
    def execute_plugin(self, path: str, path_to: str):
        yield copy_entry(path=path, path_to=path_to)


class MoveFiles:
    def execute_plugin(self, path: str, path_to: str):
        yield move_entry(path=path, path_to=path_to)


class RemoveFiles:
    def execute_plugin(self, path, patterns: List[str] = []):
        remove_entry(path, patterns=patterns)


class UpdateFileMode:
    def execute_plugin(self, path: str, mode: str):
        update_entry_mode(path=path, mode=mode)


class CreateFiles:
    def execute_plugin(self, path: str, content: AnyStr):
        write_entry(path=path, content=content)


class ArchiveFiles:
    def execute_plugin(self, path: str, archive: str, format: str):
        archive_entry(path=path, archive=archive, format=format)


class UnarchiveFiles:
    def execute_plugin(self, archive: str, path: str):
        unarchive_entry(archive=archive, path=path)


class MatchFileContent:
    def execute_plugin(self, path: str, patterns: List[str]):
        for line, matches in entry_content_contains(
            path=path, patterns=patterns
        ).items():
            yield {line: matches}


class CreateExecutableFile:
    def execute_plugin(self, path: str, content: AnyStr):
        write_entry(path=path, content=content)


class UpdateExecutableFileMode:
    def execute_plugin(self, path: str, mode: str):
        update_entry_mode(path=path, mode=mode)


class ExecuteFile:
    def execute_plugin(self, entry: str, pre: List[str], wait: bool):
        execute(entry=entry, pre=pre, wait=wait)
