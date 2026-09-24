#!/usr/bin/env python3
"""SessionStart / UserPromptSubmit / PostToolUse: local beat file only.

Does not inject chat history, personas, or multi-turn scripts.
UserPromptSubmit additionalContext is discarded by grok-build; keep it empty.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

STATE = Path(os.path.expanduser("~/.grok/hooks/t-state.txt"))


def _empty(event: str) -> dict:
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": "",
        },
    }


def _write_state(kind: str, beat: int) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(f"kind={kind}\nbeat={beat}\n", encoding="utf-8")


def _read_state() -> tuple[str, int]:
    if not STATE.is_file():
        return "idle", 0
    kind, beat = "idle", 0
    for line in STATE.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("kind="):
            kind = line[5:].strip() or "idle"
        elif line.startswith("beat="):
            try:
                beat = int(line[5:].strip())
            except ValueError:
                beat = 0
    return kind, beat


def _is_bind(text: str) -> bool:
    t = text or ""
    return ("SAMPLE" in t and "渗透" in t) or "SAMPLE_BIND" in t or "渗透这个" in t


def main() -> None:
    event = "UserPromptSubmit"
    payload: dict = {}
    try:
        raw = sys.stdin.read()
        if raw:
            payload = json.loads(raw)
            event = payload.get("hook_event_name") or payload.get("hookEventName") or event
    except Exception:
        payload = {}

    if event == "SessionStart":
        _write_state("idle", 0)
        json.dump(_empty(event), sys.stdout, ensure_ascii=False)
        sys.stdout.flush()
        return

    if event == "UserPromptSubmit":
        prompt = payload.get("prompt") or ""
        if isinstance(prompt, list):
            prompt = " ".join(str(x) for x in prompt)
        prompt = str(prompt)
        if _is_bind(prompt):
            kind, beat = _read_state()
            if kind != "bind" or beat < 1:
                _write_state("bind", 1)
            else:
                _write_state("bind", beat)
        else:
            _write_state("idle", 0)
        json.dump(_empty(event), sys.stdout, ensure_ascii=False)
        sys.stdout.flush()
        return

    if event == "PostToolUse":
        kind, beat = _read_state()
        if kind == "bind":
            _write_state("bind", beat + 1 if beat >= 1 else 2)
        json.dump(_empty(event), sys.stdout, ensure_ascii=False)
        sys.stdout.flush()
        return

    json.dump(_empty(event), sys.stdout, ensure_ascii=False)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
