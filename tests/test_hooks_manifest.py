"""Sanity check for the plugin's `hooks/hooks.json`.

The wrapper shape checked here (`{"hooks": {"<Event>": [{"hooks": [...]}]}}`)
is the plugin-specific hooks format, verified against several currently
installed Claude Code plugins (ralph-loop, security-guidance, superpowers,
codex, explanatory-output-style) and against the official `plugin-dev`
skill's hook-development reference -- not a guess.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_hooks_json_is_valid_and_registers_session_start():
    manifest_path = REPO_ROOT / "hooks" / "hooks.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    session_start = manifest["hooks"]["SessionStart"]
    assert isinstance(session_start, list) and session_start

    commands = [
        hook["command"]
        for entry in session_start
        for hook in entry["hooks"]
        if hook.get("type") == "command"
    ]
    assert any("restore-memory-symlink.sh" in command for command in commands)


def test_the_referenced_hook_script_exists_and_is_a_shell_script():
    script_path = REPO_ROOT / "hooks" / "restore-memory-symlink.sh"
    assert script_path.is_file()
    assert script_path.read_text(encoding="utf-8").startswith("#!/bin/bash")
