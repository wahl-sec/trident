#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tests.fixtures.trident_daemon import *

from pathlib import Path
from json import load


def test_runner_store_sync(trident_daemon_sync):
    trident_daemon_sync.start_all_runners()
    trident_daemon_sync.wait_for_runners()
    for runner in trident_daemon_sync._future_runners.values():
        store_path = runner.data_daemon.daemon_config.store_path
        assert Path(store_path).exists()
        with open(store_path, "r") as store_obj:
            assert load(store_obj)


def test_runner_store_async(trident_daemon_async):
    trident_daemon_async.start_all_runners()
    trident_daemon_async.wait_for_runners()
    for runner in trident_daemon_async._future_runners.values():
        store_path = runner.data_daemon.daemon_config.store_path
        assert Path(store_path).exists()
        with open(store_path, "r") as store_obj:
            assert load(store_obj)


def test_global_store_sync(trident_daemon_sync_global):
    trident_daemon_sync_global.start_all_runners()
    trident_daemon_sync_global.wait_for_runners()
    for runner in trident_daemon_sync_global._future_runners.values():
        store_path = runner.data_daemon.daemon_config.store_path
        assert Path(store_path).exists()
        with open(store_path, "r") as store_obj:
            assert load(store_obj)


def test_global_store_async(trident_daemon_async_global):
    trident_daemon_async_global.start_all_runners()
    trident_daemon_async_global.wait_for_runners()
    runners = iter(trident_daemon_async_global._future_runners.values())
    global_store = next(runners).data_daemon.daemon_config.store_path
    assert Path(global_store).exists()
    with open(global_store, "r") as store_obj:
        assert load(store_obj)

    try:
        while True:
            runner = next(runners)
            assert runner.data_daemon.daemon_config.store_path == global_store
    except StopIteration:
        pass


def test_no_store_sync(trident_daemon_sync_no_store):
    trident_daemon_sync_no_store.start_all_runners()
    trident_daemon_sync_no_store.wait_for_runners()
    runner = next(iter(trident_daemon_sync_no_store._future_runners.values()))
    assert runner.data_daemon is None


def test_no_store_async(trident_daemon_async_no_store):
    trident_daemon_async_no_store.start_all_runners()
    trident_daemon_async_no_store.wait_for_runners()
    runner = next(iter(trident_daemon_async_no_store._future_runners.values()))
    assert runner.data_daemon is None


def test_invalid_store_arguments_sync(trident_daemon_invalid_argument_store_sync):
    trident_daemon_invalid_argument_store_sync.start_all_runners()
    trident_daemon_invalid_argument_store_sync.wait_for_runners()
    runner = next(
        iter(trident_daemon_invalid_argument_store_sync._future_runners.values())
    )
    assert runner.data_daemon is None


def test_invalid_store_arguments_async(trident_daemon_invalid_argument_store_async):
    trident_daemon_invalid_argument_store_async.start_all_runners()
    trident_daemon_invalid_argument_store_async.wait_for_runners()
    runner = next(
        iter(trident_daemon_invalid_argument_store_async._future_runners.values())
    )
    assert runner.data_daemon is None
