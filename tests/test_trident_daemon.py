#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tests.fixtures.trident_daemon import *

from trident.lib.runner.trident import TridentRunner


def test_initialize_daemon(trident_daemon_sync):
    assert len(trident_daemon_sync.runners) == 1
    assert trident_daemon_sync.daemon_config.plugins["test0"]["path"] == "tests.plugins.test_plugin"

def test_run_plugin_sync(trident_daemon_sync):
    assert trident_daemon_sync._future_runners is None
    trident_daemon_sync.start_all_runners()
    trident_daemon_sync.wait_for_runners()
    for runner in trident_daemon_sync._future_runners.values():
        assert len(runner.data_daemon.store_data["runners"][runner.runner_id]["results"]["0"].keys()) == 10

def test_run_plugin_async(trident_daemon_async):
    assert trident_daemon_async._future_runners is None
    trident_daemon_async.start_all_runners()
    trident_daemon_async.wait_for_runners()
    assert all([isinstance(runner, TridentRunner) for runner in trident_daemon_async._future_runners.values()])
    for runner in trident_daemon_async._future_runners.values():
        assert len(runner.data_daemon.store_data["runners"][runner.runner_id]["results"]["0"].keys()) == 10
