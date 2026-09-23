#!/usr/bin/env python3
"""SessionStart / UserPromptSubmit: continue only. No overlay text.

Grok 4.7 treats checksum rituals and persona preambles as identity override.
Keep this hook silent so the ticket and AGENTS.md carry delivery format.
"""
import json
import sys


def main():
    event = "UserPromptSubmit"
    try:
        raw = sys.stdin.read()
        if raw:
            payload = json.loads(raw)
            event = payload.get("hook_event_name") or payload.get("hookEventName") or event
    except Exception:
        pass
    out = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": "",
        },
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
