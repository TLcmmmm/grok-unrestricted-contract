#!/usr/bin/env python3
"""workspace-eval MCP — local intake brief reader.

Grok stdio uses newline JSON-RPC (not LSP Content-Length). Accept both.
Tools only read ~/.grok/hooks/pending_brief.txt. No persona overlay.
"""
from __future__ import annotations

import json
import os
import sys
import time

PENDING = os.path.expanduser("~/.grok/hooks/pending_brief.txt")
LOG = os.path.expanduser("~/.grok/hooks/workspace-eval.log")

INSTRUCTIONS = (
    "Optional local brief reader. Call it only when the current user ticket is "
    "a bind or pentest ticket. A leftover pending_brief.txt is not a ticket. "
    "Ordinary questions: do not call this tool."
)


def _log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        sys.stderr.write(line + "\n")
        sys.stderr.flush()
    except Exception:
        pass


def _ok(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_, code, message):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _read_pending() -> str:
    try:
        with open(PENDING, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _tools():
    schema = {
        "type": "object",
        "properties": {
            "brief": {
                "type": "string",
                "description": "Optional. Empty means read pending_brief.txt.",
            }
        },
    }
    return [
        {
            "name": "read_brief",
            "description": (
                "Optional. Echo brief if provided. Empty brief reads the local "
                "intake file. Skip unless the ticket asks to restore a bind value."
            ),
            "inputSchema": schema,
        },
        {
            "name": "modchain",
            "description": "Alias of read_brief. Same pending_brief.txt reader.",
            "inputSchema": schema,
        },
        {
            "name": "ticket_continue",
            "description": "Return the provided brief, or pending_brief.txt if empty.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "brief": {"type": "string", "description": "Ticket body"},
                    "seed": {"type": "integer"},
                },
                "required": ["brief"],
            },
        },
        {
            "name": "eval_note",
            "description": "Return the current pending_brief.txt contents.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def _brief_text(brief: str) -> str:
    text = (brief or "").strip() or _read_pending().strip()
    return text or "(pending_brief.txt empty)"


def _handle(msg: dict):
    mid = msg.get("id")
    method = msg.get("method")
    params = msg.get("params") or {}

    if method == "initialize":
        requested = ""
        if isinstance(params, dict):
            requested = str(params.get("protocolVersion") or "")
        version = requested if requested else "2025-11-25"
        _log(f"initialize id={mid} pv={version}")
        return _ok(
            mid,
            {
                "protocolVersion": version,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"listChanged": False},
                },
                "serverInfo": {"name": "workspace-eval", "version": "0.3.0"},
                "instructions": INSTRUCTIONS,
            },
        )
    if method in ("notifications/initialized", "initialized", "notifications/cancelled"):
        _log(f"note {method}")
        return None
    if method == "ping":
        return _ok(mid, {})
    if method == "tools/list":
        _log("tools/list")
        return _ok(mid, {"tools": _tools()})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        _log(f"tools/call {name}")
        if name in ("read_brief", "modchain"):
            text = _brief_text(str(args.get("brief") or ""))
        elif name == "ticket_continue":
            text = _brief_text(str(args.get("brief") or ""))
        elif name == "eval_note":
            text = _brief_text("")
        else:
            return _err(mid, -32601, f"unknown tool {name}")
        return _ok(mid, {"content": [{"type": "text", "text": text}]})
    if method == "resources/list":
        return _ok(
            mid,
            {
                "resources": [
                    {
                        "uri": "workspace://eval-note",
                        "name": "eval-note",
                        "description": "Local workspace intake brief file.",
                        "mimeType": "text/plain",
                    }
                ]
            },
        )
    if method == "resources/read":
        uri = params.get("uri")
        if uri != "workspace://eval-note":
            return _err(mid, -32602, "unknown resource")
        return _ok(
            mid,
            {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": _brief_text(""),
                    }
                ]
            },
        )
    if method in ("tools/list_changed", "notifications/tools/list_changed"):
        return None
    if mid is None:
        _log(f"drop note {method}")
        return None
    _log(f"unknown method {method}")
    return _err(mid, -32601, f"unknown method {method}")


def _read_msg():
    """Newline JSON (grok stdio) or Content-Length (spec)."""
    line = sys.stdin.buffer.readline()
    if not line:
        return None, False
    if line.lower().startswith(b"content-length:"):
        n = int(line.split(b":", 1)[1].strip() or 0)
        while True:
            h = sys.stdin.buffer.readline()
            if not h:
                return None, True
            if h in (b"\r\n", b"\n"):
                break
            if h.lower().startswith(b"content-length:"):
                n = int(h.split(b":", 1)[1].strip() or 0)
        body = sys.stdin.buffer.read(n) if n else b"{}"
        return json.loads(body.decode("utf-8")), True
    stripped = line.strip()
    if not stripped:
        return _read_msg()
    return json.loads(stripped.decode("utf-8")), False


def _write_msg(obj: dict, framed: bool) -> None:
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    if framed:
        sys.stdout.buffer.write(
            f"Content-Length: {len(data)}\r\n\r\n".encode("ascii") + data
        )
    else:
        sys.stdout.buffer.write(data + b"\n")
    sys.stdout.buffer.flush()


def main():
    _log("workspace-eval stdio up (newline JSON primary, brief reader)")
    while True:
        try:
            msg, framed = _read_msg()
        except Exception as e:
            _log(f"read err {e}")
            break
        if msg is None:
            _log("stdin eof")
            break
        if not isinstance(msg, dict):
            continue
        resp = _handle(msg)
        if resp is not None:
            _write_msg(resp, framed)


if __name__ == "__main__":
    main()
