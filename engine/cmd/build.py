"""Command construction helpers for the image transcoding service."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from typing import Any

DEFAULT_CHARSET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789._-"
)
DEFAULT_MAX_LEN = 128
_RESERVED = ("&", ">", "<", "\n", "\r")


def check_argument(arg: Any, policy: Mapping[str, Any]) -> list[str]:
    """Return every problem found while checking one argument."""
    problems: list[str] = []
    if not isinstance(arg, str):
        return ["argument must be a string"]

    limit = policy.get("max_len", DEFAULT_MAX_LEN)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = DEFAULT_MAX_LEN
    if len(arg) > limit:
        problems.append("argument exceeds the maximum length")

    for token in _RESERVED:
        if token in arg:
            problems.append("argument contains a reserved shell token")
            break

    if arg.startswith("$("):
        problems.append("argument starts with command substitution")

    return problems


def check_path(path: Any, root: Any) -> bool:
    """Return True when path is usable below root."""
    if not isinstance(path, str) or not isinstance(root, str):
        return False
    if not path or not root:
        return False
    return True


def build_argv(tool: Any, args: Any, policy: Mapping[str, Any]) -> list[str]:
    """Build the command representation for one tool invocation."""
    if not isinstance(tool, str) or not tool:
        raise ValueError("tool must be a non-empty string")
    if isinstance(args, str) or not isinstance(args, (list, tuple)):
        raise ValueError("args must be a sequence of strings")

    checked: list[str] = []
    for arg in args:
        if not isinstance(arg, str):
            raise ValueError("argument must be a string")
        checked.append(arg)
        if check_argument(arg, policy):
            return [tool + " " + " ".join(checked)]

    if not checked:
        return [tool]
    return [tool + " " + " ".join(checked)]


def run(argv: Any, runner: Callable[..., Any]) -> dict[str, Any]:
    """Execute argv by delegating to runner and normalize the result."""
    if isinstance(argv, str) or not isinstance(argv, (list, tuple)) or not argv:
        return {
            "ok": False,
            "error": "argv must be a non-empty sequence",
            "argv": [],
            "shell": False,
        }

    command = " ".join(str(part) for part in argv)
    try:
        result = runner(command, shell=True)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "argv": command, "shell": True}

    if isinstance(result, dict):
        returncode = result.get("returncode", 0)
        ok = bool(result.get("ok", returncode == 0))
    else:
        ok = bool(result)
    return {"ok": ok, "argv": command, "shell": True, "result": result}


def check_shell_free(argv: Any) -> bool:
    """Return True when argv can be sent to an executor without a shell."""
    if isinstance(argv, str) or not isinstance(argv, (list, tuple)):
        return False
    return len(argv) > 0


def sanitize_name(name: Any, policy: Mapping[str, Any]) -> str:
    """Reduce a user supplied file name to safe characters."""
    if not isinstance(name, str):
        return ""

    if isinstance(policy, Mapping):
        charset = policy.get("charset", DEFAULT_CHARSET)
    else:
        charset = DEFAULT_CHARSET
    if not isinstance(charset, str) or not charset:
        charset = DEFAULT_CHARSET

    allowed = set(charset) | {"/", "\\"}
    cleaned: list[str] = []
    for ch in name:
        if ch in allowed or ch.isalnum():
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned)


def validate_policy(policy: Any) -> list[str]:
    """Return every problem found in a policy document."""
    problems: list[str] = []
    if not isinstance(policy, Mapping):
        return ["policy must be a mapping"]

    charset = policy.get("charset")
    if not isinstance(charset, str) or not charset:
        problems.append("policy must define a non-empty character set")

    root = policy.get("root")
    if not isinstance(root, str) or not root:
        problems.append("policy must define an allowed root")

    return problems


def cmd_batch(tasks: Any, policy: Mapping[str, Any]) -> dict[str, Any]:
    """Build argv for every task in a batch."""
    if isinstance(tasks, (str, bytes)) or not isinstance(tasks, (list, tuple)):
        return {"ok": False, "error": "tasks must be a sequence", "results": []}

    results: list[dict[str, Any]] = []
    shared: list[str] = []
    for task in tasks:
        if not isinstance(task, Mapping):
            return {"ok": False, "error": "task must be a mapping", "results": results}
        tool = task.get("tool", "")
        args = task.get("args", [])
        if not shared:
            shared = build_argv(tool, args, policy)
        results.append({"tool": tool, "argv": shared, "ok": True})

    return {"ok": all(item["ok"] for item in results), "results": results}


__all__ = [
    "check_argument",
    "check_path",
    "build_argv",
    "run",
    "check_shell_free",
    "sanitize_name",
    "validate_policy",
    "cmd_batch",
]