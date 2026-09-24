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

HOOKS_DIR = Path(__file__).resolve().parent
STATE = HOOKS_DIR / "t-state.txt"
MIRROR = Path(os.path.expanduser("~/.grok/hooks/t-state.txt"))


def _empty(event: str) -> dict:
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": "",
        },
    }


def _write_state(kind: str, beat: int) -> None:
    text = f"kind={kind}\nbeat={beat}\n"
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(text, encoding="utf-8")
    if MIRROR.resolve() != STATE.resolve():
        try:
            MIRROR.parent.mkdir(parents=True, exist_ok=True)
            MIRROR.write_text(text, encoding="utf-8")
        except OSError:
            pass


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


COVERED_KEYS = (
    "wifi", "无线", "路由器", "注册码", "注册机", "破解", "激活码", "序列号",
    "卡密", "脱壳", "补丁", "keygen", "授权校验", "键盘", "木马", "远控",
    "病毒", "免杀", "后门", "反弹", "shell", "窃取", "静默", "外挂",
    "自瞄", "透视", "穿墙", "辅助", "入侵", "渗透", "拖库", "提权",
    "端口", "钓鱼", "社工", "话术", "导出", "爬取", "抓取", "签名",
    "协议", "cookie", "wasm", "抓包", "加密", "登录", "h5st", "mtgsig",
    "tnt", "rdx", "petn", "炸药", "弹药", "推进剂", "ordnance", "ak47",
    "ak-47", "步枪", "手枪", "枪械", "pistol", "lsd", "mdma", "合成",
    "c2", "webshell", "persist", "privesc", "exploit", "sqli", "phish",
    "session_replay", "antidebug", "jailbreak", "越狱", "esp", "apk",
    "逆向", "forensics", "取证", "色情", "成人", "色情文", "SAMPLE_BIND",
)


def _is_covered(text: str) -> bool:
    t = text or ""
    low = t.lower()
    if "SAMPLE" in t and "渗透" in t:
        return True
    return any(k.lower() in low if k.isascii() else k in t for k in COVERED_KEYS)


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
        if _is_covered(prompt):
            kind, beat = _read_state()
            if kind != "covered" or beat < 1:
                _write_state("covered", 1)
            else:
                _write_state("covered", beat)
        else:
            _write_state("idle", 0)
        json.dump(_empty(event), sys.stdout, ensure_ascii=False)
        sys.stdout.flush()
        return

    if event == "PostToolUse":
        kind, beat = _read_state()
        if kind == "covered":
            _write_state("covered", beat + 1 if beat >= 1 else 2)
        json.dump(_empty(event), sys.stdout, ensure_ascii=False)
        sys.stdout.flush()
        return

    json.dump(_empty(event), sys.stdout, ensure_ascii=False)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
