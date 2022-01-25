#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tests.fixtures.trident_daemon import *


def test_entries(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "files0":
            assert (
                len(
                    runner.data_daemon.store_data["runners"][runner.runner_id][
                        "results"
                    ]["0"].keys()
                )
                == 2
            )


def test_remove_entry(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "files0":
            first, second = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert {first["name"], second["name"]} == {"test", "test1"}
            runner.start_runner()
            first, second = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert {first["name"], second["name"]} == {"test", "files0.json"}
            break


def test_move_entry(trident_daemon_files_sync):
    pass


def test_copy_entry(trident_daemon_files_sync):
    pass


def test_update_entry_mode(trident_daemon_files_sync):
    pass


def test_write_entry(trident_daemon_files_sync):
    pass


def test_archive_entry(trident_daemon_files_sync):
    pass


def test_unarchive_entry(trident_daemon_files_sync):
    pass


def test_entry_content_contains(trident_daemon_files_sync):
    pass


def test_execute_entry(trident_daemon_files_sync):
    pass
