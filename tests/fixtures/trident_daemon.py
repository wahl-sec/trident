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
                    },
                }
            },
        )
    )


@pytest.fixture
def trident_daemon_files_sync(tmpdir):
    tmpdir.mkdir("test")
    tmpdir.mkdir("test1")
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1,
            plugins={
                "files0": {
                    "path": "plugins.files.find_files",
                    "plugin_args": {"path": tmpdir},
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                    },
                },
                "files1": {
                    "path": "plugins.files.remove_files",
                    "plugin_args": {"path": tmpdir, "pattern": ["test1"]},
                    "args": {
                        "store": {
                            "path_store": tmpdir,
                            "no_store": False,
                            "global_store": None,
                        },
                        "runner": {"dont_store_on_error": False},
                        "notification": {},
                    },
                },
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
                    },
                },
            },
        )
    )
