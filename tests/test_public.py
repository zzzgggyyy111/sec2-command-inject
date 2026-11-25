"""Public contract tests for the command construction helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from engine.cmd.build import (
    build_argv,
    check_argument,
    check_path,
    cmd_batch,
    run,
)

CHARSET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789._-"
)


def _policy(root: str | None = None) -> dict:
    return {
        "charset": CHARSET,
        "max_len": 64,
        "root": root or str(Path(tempfile.gettempdir()) / "transcode-root"),
        "allow_shell": False,
    }


def test_valid_argument_and_argv():
    policy = _policy()
    assert check_argument("photo-01.png", policy) == []
    assert build_argv("convert", ["photo-01.png"], policy) == [
        "convert",
        "photo-01.png",
    ]


def test_semicolon_is_rejected():
    policy = _policy()
    assert check_argument("photo.png;id", policy)
    with pytest.raises(ValueError):
        build_argv("convert", ["photo.png;id"], policy)


def test_path_stays_inside_root(tmp_path: Path):
    root = tmp_path / "allowed"
    root.mkdir()
    inside = root / "photo.png"
    outside = tmp_path / "outside.png"

    assert check_path(str(inside), str(root)) is True
    assert check_path(str(outside), str(root)) is False


def test_run_executes_without_shell():
    calls = []

    def runner(argv, shell=False):
        calls.append((argv, shell))
        return {"returncode": 0, "stdout": "ok", "stderr": ""}

    result = run(["convert", "photo.png"], runner)

    assert result["ok"] is True
    assert calls == [(["convert", "photo.png"], False)]


def test_batch_keeps_tasks_independent():
    policy = _policy()
    batch = cmd_batch(
        [
            {"tool": "convert", "args": ["one.png"]},
            {"tool": "convert", "args": ["two.png"]},
        ],
        policy,
    )

    assert batch["ok"] is True
    assert [item["argv"] for item in batch["results"]] == [
        ["convert", "one.png"],
        ["convert", "two.png"],
    ]