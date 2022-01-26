#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pytest

from pathlib import Path

from tests.fixtures.trident_daemon import *


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [("find_files")],
    indirect=["trident_daemon_files_sync"],
)
def test_entries(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "find_files":
            assert (
                len(
                    runner.data_daemon.store_data["runners"][runner.runner_id][
                        "results"
                    ]["0"].keys()
                )
                == 2
            )


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [("remove_files")],
    indirect=["trident_daemon_files_sync"],
)
def test_remove_entry(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "find_files":
            first, second = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert {first["name"], second["name"]} == {"test", "test1"}
            runner.start_runner()
            first, second = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert {first["name"], second["name"]} == {"test", "find_files.json"}
            break


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [("find_files", "move_files")],
    indirect=["trident_daemon_files_sync"],
)
def test_move_entry(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()

    _find_files_runner = None
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "find_files":
            _find_files_runner = runner
            first, second = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert {first["name"], second["name"]} == {"test", "test1"}

        if runner.runner_id == "move_files":
            (result,) = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert Path(result).name == "new"
            _find_files_runner.start_runner()
            results = _find_files_runner.data_daemon.store_data["runners"][
                "find_files"
            ]["results"]["0"].values()
            assert all(result["name"] != "test" for result in results)
            assert any(result["name"] == "new" for result in results)


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [("find_files", "copy_files")],
    indirect=["trident_daemon_files_sync"],
)
def test_copy_entry(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()

    _find_files_runner = None
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "find_files":
            _find_files_runner = runner
            first, second = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert {first["name"], second["name"]} == {"test", "test1"}

        if runner.runner_id == "copy_files":
            (result,) = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert Path(result).name == "copy"
            _find_files_runner.start_runner()
            results = _find_files_runner.data_daemon.store_data["runners"][
                "find_files"
            ]["results"]["0"].values()
            assert any(result["name"] == "test" for result in results)
            assert any(result["name"] == "copy" for result in results)


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [("find_file", "update_file_mode")],
    indirect=["trident_daemon_files_sync"],
)
def test_update_entry_mode(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()

    _find_file_runner = None
    _prev_mode = None
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "find_file":
            _find_file_runner = runner
            (_file,) = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            _prev_mode = _file["stat"]["mode"]

        if runner.runner_id == "update_file_mode":
            _find_file_runner.start_runner()
            (_file,) = _find_file_runner.data_daemon.store_data["runners"]["find_file"][
                "results"
            ]["0"].values()
            _new_mode = _file["stat"]["mode"]
            assert _new_mode == "0o40777"
            assert _new_mode != _prev_mode


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [("find_files", "create_files")],
    indirect=["trident_daemon_files_sync"],
)
def test_write_entry(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()

    _find_files_runner = None
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "find_files":
            _find_files_runner = runner
            first, second = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert {first["name"], second["name"]} == {"test", "test1"}

        if runner.runner_id == "create_files":
            _find_files_runner.start_runner()
            results = _find_files_runner.data_daemon.store_data["runners"][
                "find_files"
            ]["results"]["0"].values()
            assert any(result["name"] == "write.txt" for result in results)


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [("find_files", "archive_files")],
    indirect=["trident_daemon_files_sync"],
)
def test_archive_entry(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()

    _find_files_runner = None
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "find_files":
            _find_files_runner = runner
            first, second = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert {first["name"], second["name"]} == {"test", "test1"}

        if runner.runner_id == "archive_files":
            _find_files_runner.start_runner()
            results = _find_files_runner.data_daemon.store_data["runners"][
                "find_files"
            ]["results"]["0"].values()
            assert any(result["name"] == "archive.tar.gz" for result in results)


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [("find_files", "archive_files", "unarchive_files")],
    indirect=["trident_daemon_files_sync"],
)
def test_unarchive_entry(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()

    _find_files_runner = None
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "find_files":
            _find_files_runner = runner
            first, second = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert {first["name"], second["name"]} == {"test", "test1"}

        if runner.runner_id == "archive_files":
            _find_files_runner.start_runner()
            results = _find_files_runner.data_daemon.store_data["runners"][
                "find_files"
            ]["results"]["0"].values()
            assert any(result["name"] == "archive.tar.gz" for result in results)

        if runner.runner_id == "unarchive_files":
            _find_files_runner.start_runner()
            results = _find_files_runner.data_daemon.store_data["runners"][
                "find_files"
            ]["results"]["0"].values()
            assert any(result["name"] == "out" for result in results)


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [("create_files", "match_file_content")],
    indirect=["trident_daemon_files_sync"],
)
def test_entry_content_contains(trident_daemon_files_sync):
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()

    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "match_file_content":
            (result,) = runner.data_daemon.store_data["runners"][runner.runner_id][
                "results"
            ]["0"].values()
            assert len(result[1]) == 1

            (match,) = result[1]
            assert match["line"] == "Hello, this is a text"


@pytest.mark.parametrize(
    "trident_daemon_files_sync",
    [
        (
            "create_executable_file",
            "update_executable_file_mode",
            "find_files",
            "execute_file",
        )
    ],
    indirect=["trident_daemon_files_sync"],
)
def test_execute_entry(trident_daemon_files_sync):
    # TODO: Support This test does not work on Windows because of /bin/sh, so we should implement another test for Windows
    assert trident_daemon_files_sync._future_runners is None
    trident_daemon_files_sync.start_all_runners()
    trident_daemon_files_sync.wait_for_runners()

    _find_files_runner = None
    for runner in trident_daemon_files_sync._future_runners.values():
        if runner.runner_id == "find_files":
            _find_files_runner = runner
            results = runner.data_daemon.store_data["runners"]["find_files"]["results"][
                "0"
            ].values()
            assert all(result["name"] != "script_file" for result in results)

        if runner.runner_id == "execute_file":
            _find_files_runner.start_runner()
            results = _find_files_runner.data_daemon.store_data["runners"][
                "find_files"
            ]["results"]["0"].values()
            assert any(result["name"] == "script_file" for result in results)
