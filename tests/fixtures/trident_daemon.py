#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

from trident.lib.daemon.trident import TridentDaemonConfig, TridentDaemon

@pytest.fixture
def trident_daemon_sync(tmpdir):
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1, plugins={"test0": {"path": "tests.plugins.test_plugin"}},
            data_config={
                "path_store": tmpdir,
                "no_store": False,
                "global_store": None
            }, dont_store_on_error=False
        )
    )

@pytest.fixture
def trident_daemon_async(tmpdir):
    return TridentDaemon(
        TridentDaemonConfig(
            workers=5, plugins={
                "test0": {"path": "tests.plugins.test_plugin"},
                "test1": {"path": "tests.plugins.test_plugin"},
                "test2": {"path": "tests.plugins.test_plugin"},
                "test3": {"path": "tests.plugins.test_plugin"},
                "test4": {"path": "tests.plugins.test_plugin"},
            }, data_config={
                "path_store": tmpdir,
                "no_store": False,
                "global_store": None
            }, dont_store_on_error=False
        )
    )

@pytest.fixture
def trident_daemon_sync_global(tmpdir):
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1, plugins={"test0": {"path": "tests.plugins.test_plugin"}},
            data_config={
                "path_store": tmpdir,
                "no_store": False,
                "global_store": "global.json"
            }, dont_store_on_error=False
        )
    )

@pytest.fixture
def trident_daemon_async_global(tmpdir):
    return TridentDaemon(
        TridentDaemonConfig(
            workers=5, plugins={
                "test0": {"path": "tests.plugins.test_plugin"},
                "test1": {"path": "tests.plugins.test_plugin"},
                "test2": {"path": "tests.plugins.test_plugin"},
                "test3": {"path": "tests.plugins.test_plugin"},
                "test4": {"path": "tests.plugins.test_plugin"},
            }, data_config={
                "path_store": tmpdir,
                "no_store": False,
                "global_store": "global.json"
            }, dont_store_on_error=False
        )
    )

@pytest.fixture
def trident_daemon_sync_no_store():
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1, plugins={"test0": {"path": "tests.plugins.test_plugin"}},
            data_config={
                "path_store": None,
                "no_store": True,
                "global_store": None
            }, dont_store_on_error=False
        )
    )

@pytest.fixture
def trident_daemon_async_no_store():
    return TridentDaemon(
        TridentDaemonConfig(
            workers=5, plugins={
                "test0": {"path": "tests.plugins.test_plugin"},
                "test1": {"path": "tests.plugins.test_plugin"},
                "test2": {"path": "tests.plugins.test_plugin"},
                "test3": {"path": "tests.plugins.test_plugin"},
                "test4": {"path": "tests.plugins.test_plugin"},
            }, data_config={
                "path_store": None,
                "no_store": True,
                "global_store": None
            }, dont_store_on_error=False
        )
    )

@pytest.fixture
def trident_daemon_invalid_argument_store_sync():
    return TridentDaemon(
        TridentDaemonConfig(
            workers=1, plugins={
                "test0": {"path": "tests.plugins.test_plugin"},
            }, data_config={
                "path_store": None,
                "no_store": True,
                "global_store": "global.json"
            }, dont_store_on_error=False
        )
    )

@pytest.fixture
def trident_daemon_invalid_argument_store_async():
    return TridentDaemon(
        TridentDaemonConfig(
            workers=5, plugins={
                "test0": {"path": "tests.plugins.test_plugin"},
                "test1": {"path": "tests.plugins.test_plugin"},
                "test2": {"path": "tests.plugins.test_plugin"},
                "test3": {"path": "tests.plugins.test_plugin"},
                "test4": {"path": "tests.plugins.test_plugin"},
            }, data_config={
                "path_store": None,
                "no_store": True,
                "global_store": "global.json"
            }, dont_store_on_error=False
        )
    )
