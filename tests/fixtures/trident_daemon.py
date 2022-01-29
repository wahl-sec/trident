#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

from trident.lib.daemon.trident import TridentDaemonConfig, TridentDaemon


@pytest.fixture
def trident_daemon_sync(tmpdir):
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1,
            plugins={
                "test0": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                }
            },
        )
    )


@pytest.fixture
def trident_daemon_files_sync(request, tmpdir):
    tmpdir.mkdir("test")
    tmpdir.mkdir("test1")
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1,
            plugins={
                plugin: config
                for plugin, config in {
                    "find_files": {
                        "path": "tests.plugins.files.files",
                        "name": "FindFiles",
                        "plugin_args": {"path": tmpdir},
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "find_file": {
                        "path": "tests.plugins.files.files",
                        "name": "FindFile",
                        "plugin_args": {"path": tmpdir},
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "remove_files": {
                        "path": "tests.plugins.files.files",
                        "name": "RemoveFiles",
                        "plugin_args": {"path": tmpdir, "patterns": ["test1"]},
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "move_files": {
                        "path": "tests.plugins.files.files",
                        "name": "MoveFiles",
                        "plugin_args": {
                            "path": f"{tmpdir}/test",
                            "path_to": f"{tmpdir}/new",
                        },
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "copy_files": {
                        "path": "tests.plugins.files.files",
                        "name": "CopyFiles",
                        "plugin_args": {
                            "path": f"{tmpdir}/test",
                            "path_to": f"{tmpdir}/copy",
                        },
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "update_file_mode": {
                        "path": "tests.plugins.files.files",
                        "name": "UpdateFileMode",
                        "plugin_args": {"path": tmpdir, "mode": "0o40777"},
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "create_files": {
                        "path": "tests.plugins.files.files",
                        "name": "CreateFiles",
                        "plugin_args": {
                            "path": f"{tmpdir}/write.txt",
                            "content": "Hello, this is a text",
                        },
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "archive_files": {
                        "path": "tests.plugins.files.files",
                        "name": "ArchiveFiles",
                        "plugin_args": {
                            "path": [f"{tmpdir}/test", f"{tmpdir}/test1"],
                            "archive": f"{tmpdir}/archive.tar.gz",
                            "format": "gz",
                        },
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "unarchive_files": {
                        "path": "tests.plugins.files.files",
                        "name": "UnarchiveFiles",
                        "plugin_args": {
                            "archive": f"{tmpdir}/archive.tar.gz",
                            "path": f"{tmpdir}/out",
                        },
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "match_file_content": {
                        "path": "tests.plugins.files.files",
                        "name": "MatchFileContent",
                        "plugin_args": {
                            "path": f"{tmpdir}/write.txt",
                            "patterns": ["Hello.*"],
                        },
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "create_executable_file": {
                        "path": "tests.plugins.files.files",
                        "name": "CreateExecutableFile",
                        "plugin_args": {
                            "path": f"{tmpdir}/script.sh",
                            "content": f"touch {tmpdir}/script_file",
                        },
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "update_executable_file_mode": {
                        "path": "tests.plugins.files.files",
                        "name": "UpdateExecutableFileMode",
                        "plugin_args": {
                            "path": f"{tmpdir}/script.sh",
                            "mode": "0o111777",
                        },
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "execute_file": {
                        "path": "tests.plugins.files.files",
                        "name": "ExecuteFile",
                        "plugin_args": {
                            "entry": f"{tmpdir}/script.sh",
                            "pre": ["/bin/sh"],
                            "wait": True,
                        },
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                    "find_filesystems": {
                        "path": "tests.plugins.filesystem.filesystem",
                        "name": "FindFileSystem",
                        "plugin_args": {},
                        "args": {
                            "store": {
                                "path_store": tmpdir,
                                "no_store": False,
                                "global_store": None,
                            },
                            "runner": {"dont_store_on_error": False},
                            "notification": {},
                            "checkpoint": {},
                        },
                    },
                }.items()
                if plugin in request.param
            },
        )
    )


@pytest.fixture
def trident_daemon_async(tmpdir):
    return TridentDaemon(
        TridentDaemonConfig(
            workers=5,
            plugins={
                "test0": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test1": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test2": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test3": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test4": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
            },
        )
    )


@pytest.fixture
def trident_daemon_sync_global(tmpdir):
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1,
            plugins={
                "test0": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": f"{tmpdir}/global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                }
            },
        )
    )


@pytest.fixture
def trident_daemon_async_global(tmpdir):
    return TridentDaemon(
        TridentDaemonConfig(
            workers=5,
            plugins={
                "test0": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": f"{tmpdir}/global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test1": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": f"{tmpdir}/global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test2": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": f"{tmpdir}/global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test3": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": f"{tmpdir}/global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test4": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": f"{tmpdir}/global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
            },
        )
    )


@pytest.fixture
def trident_daemon_sync_no_store():
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1,
            plugins={
                "test0": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                }
            },
        )
    )


@pytest.fixture
def trident_daemon_async_no_store():
    return TridentDaemon(
        TridentDaemonConfig(
            workers=5,
            plugins={
                "test0": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test1": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test2": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test3": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test4": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
            },
        )
    )


@pytest.fixture
def trident_daemon_invalid_argument_store_sync():
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1,
            plugins={
                "test0": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": "global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                }
            },
        )
    )


@pytest.fixture
def trident_daemon_invalid_argument_store_async():
    return TridentDaemon(
        TridentDaemonConfig(
            workers=5,
            plugins={
                "test0": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": "global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test1": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": "global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test2": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": "global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test3": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": "global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
                "test4": {
                    "path": "tests.plugins.test_plugin",
                    "args": {
                        "store": {
                            "path_store": None,
                            "no_store": True,
                            "global_store": "global.json",
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                        "checkpoint": {},
                    },
                },
            },
        )
    )
