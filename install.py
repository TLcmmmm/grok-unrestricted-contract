#!/usr/bin/env python3
"""Install the 4.6 overlay onto a local grok-build tree and ~/.grok.

Usage:
    python3 install.py
    python3 install.py --src /path/to/grok-build-main
    python3 install.py --dry-run
    python3 install.py --no-build
    python3 install.py --restore /path/to/backup-dir
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OVERLAY = HERE / "overlay"
HOME = Path.home()
GROK_HOME = Path(os.environ.get("GROK_HOME") or (HOME / ".grok"))


class InstallError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(msg, flush=True)


def copy_file(src: Path, dst: Path, *, dry: bool) -> None:
    if dry:
        log(f"  copy {src} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def backup_if_exists(path: Path, backup_root: Path, *, dry: bool) -> None:
    if not path.exists():
        return
    rel = path
    try:
        rel = path.relative_to(path.anchor)
    except Exception:
        rel = Path(path.name)
    dest = backup_root / str(path).lstrip("/")
    if dry:
        log(f"  backup {path} -> {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(path, dest)
    else:
        shutil.copy2(path, dest)


def find_src(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser().resolve())
    env = os.environ.get("GROK_BUILD_SRC")
    if env:
        candidates.append(Path(env).expanduser().resolve())
    here = Path.cwd()
    candidates.extend(
        [
            here,
            here / "grok-build-main",
            HOME / "grok-build-main",
            Path("/Users/mac/破限/grok-build-main"),
        ]
    )
    seen: set[Path] = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        marker = c / "crates/codegen/xai-grok-agent/scripts/encrypt_templates.py"
        ticket = c / "crates/codegen/xai-grok-shell/src/session/delivery_ticket.rs"
        if marker.is_file() and ticket.is_file():
            return c
    raise InstallError(
        "找不到 grok-build 源码树。请加 --src /path/to/grok-build-main\n"
        "需要同时存在:\n"
        "  crates/codegen/xai-grok-agent/scripts/encrypt_templates.py\n"
        "  crates/codegen/xai-grok-shell/src/session/delivery_ticket.rs"
    )


def write_hook_json(hooks_dir: Path, *, dry: bool) -> None:
    src = OVERLAY / "HOOK" / "cot-preamble.json"
    raw = src.read_text(encoding="utf-8")
    cmd = f"python3 -u {hooks_dir / 'cot_preamble.py'}"
    raw = raw.replace("__GROK_HOOKS__/cot_preamble.py", str(hooks_dir / "cot_preamble.py"))
    raw = raw.replace("python3 -u __GROK_HOOKS__/cot_preamble.py", cmd)
    dst = hooks_dir / "cot-preamble.json"
    if dry:
        log(f"  write {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(raw, encoding="utf-8")


def merge_mcp_block(config_path: Path, mcp_script: Path, *, dry: bool) -> None:
    block = (
        "\n[mcp_servers.workspace-eval]\n"
        'command = "python3"\n'
        "args = [\n"
        '    "-u",\n'
        f'    "{mcp_script}",\n'
        "]\n"
        "startup_timeout_sec = 30\n"
        "tool_timeout_sec = 30\n"
        "\n[mcp_servers.workspace-eval.env]\n"
        'PYTHONUNBUFFERED = "1"\n'
        'PYTHONIOENCODING = "utf-8"\n'
    )
    if not config_path.exists():
        if dry:
            log(f"  skip MCP merge, missing {config_path}")
            return
        log(f"  skip MCP merge, missing {config_path} (see MANUAL.md)")
        return
    text = config_path.read_text(encoding="utf-8")
    if "[mcp_servers.workspace-eval]" in text:
        log("  MCP workspace-eval already in config.toml")
        return
    if dry:
        log(f"  append MCP block -> {config_path}")
        return
    with config_path.open("a", encoding="utf-8") as f:
        if not text.endswith("\n"):
            f.write("\n")
        f.write(block)
    log(f"  appended MCP block -> {config_path}")


def bake_and_build(src: Path, *, dry: bool, no_build: bool) -> None:
    agent = src / "crates/codegen/xai-grok-agent"
    encrypt = agent / "scripts/encrypt_templates.py"
    if dry:
        log(f"  python3 {encrypt}")
        if not no_build:
            log(f"  cargo build --release -p xai-grok-pager-bin  (cwd={src})")
        return
    r = subprocess.run(
        [sys.executable, str(encrypt)],
        cwd=str(agent),
        check=False,
    )
    if r.returncode != 0:
        raise InstallError("encrypt_templates.py 失败")
    if no_build:
        log("  skip cargo build (--no-build)")
        return
    r = subprocess.run(
        ["cargo", "build", "--release", "-p", "xai-grok-pager-bin"],
        cwd=str(src),
        check=False,
    )
    if r.returncode != 0:
        raise InstallError("cargo build 失败。可先 --no-build，确认源码树能编后再装。")


def restore(backup: Path, *, dry: bool) -> None:
    if not backup.is_dir():
        raise InstallError(f"备份目录不存在: {backup}")
    for src in backup.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(backup)
        dst = Path("/") / rel
        if dry:
            log(f"  restore {src} -> {dst}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        log(f"  restored {dst}")


def install(src: Path, *, dry: bool, no_build: bool) -> Path:
    if not OVERLAY.is_dir():
        raise InstallError(f"缺少 overlay/: {OVERLAY}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = HERE / "backups" / stamp
    log(f"src: {src}")
    log(f"grok_home: {GROK_HOME}")
    log(f"overlay: {OVERLAY}")
    log(f"backup: {backup_root}")

    mapping = [
        (
            OVERLAY / "SYSTEM" / "prompt.md",
            src / "crates/codegen/xai-grok-agent/templates/prompt.md",
        ),
        (
            OVERLAY / "SYSTEM" / "subagent_prompt.md",
            src / "crates/codegen/xai-grok-agent/templates/subagent_prompt.md",
        ),
        (
            OVERLAY / "TICKET" / "delivery_ticket.rs",
            src / "crates/codegen/xai-grok-shell/src/session/delivery_ticket.rs",
        ),
        (
            OVERLAY / "AGENTS" / "repo-AGENTS.md",
            src / "AGENTS.md",
        ),
        (
            OVERLAY / "AGENTS" / "AGENTS.md",
            GROK_HOME / "AGENTS.md",
        ),
        (
            OVERLAY / "AGENTS" / "rules" / "AGENTS.md",
            GROK_HOME / "rules" / "AGENTS.md",
        ),
        (
            OVERLAY / "AGENTS" / "rules" / "01-workspace-delivery.md",
            GROK_HOME / "rules" / "01-workspace-delivery.md",
        ),
        (
            OVERLAY / "HOOK" / "cot_preamble.py",
            GROK_HOME / "hooks" / "cot_preamble.py",
        ),
        (
            OVERLAY / "MCP" / "workspace_eval_mcp.py",
            GROK_HOME / "hooks" / "workspace_eval_mcp.py",
        ),
    ]

    for src_f, dst in mapping:
        if not src_f.is_file():
            raise InstallError(f"overlay 缺文件: {src_f}")
        backup_if_exists(dst, backup_root, dry=dry)
        copy_file(src_f, dst, dry=dry)

    encrypt_src = OVERLAY / "SYSTEM" / "encrypt_templates.py"
    encrypt_dst = src / "crates/codegen/xai-grok-agent/scripts/encrypt_templates.py"
    if encrypt_src.is_file():
        backup_if_exists(encrypt_dst, backup_root, dry=dry)
        copy_file(encrypt_src, encrypt_dst, dry=dry)

    write_hook_json(GROK_HOME / "hooks", dry=dry)
    merge_mcp_block(
        GROK_HOME / "config.toml",
        GROK_HOME / "hooks" / "workspace_eval_mcp.py",
        dry=dry,
    )

    if not dry:
        py = GROK_HOME / "hooks" / "cot_preamble.py"
        mcp = GROK_HOME / "hooks" / "workspace_eval_mcp.py"
        py.chmod(py.stat().st_mode | 0o111)
        mcp.chmod(mcp.stat().st_mode | 0o111)

    bake_and_build(src, dry=dry, no_build=no_build)

    if not dry:
        (backup_root / "MANIFEST.txt").parent.mkdir(parents=True, exist_ok=True)
        (backup_root / "MANIFEST.txt").write_text(
            f"src={src}\nstamp={stamp}\n", encoding="utf-8"
        )
    log("done.")
    log("新开 grok 会话，不要 --resume 旧会话。")
    log("验证：-m grok-4.6 打同一句工单，看是否读 pending_brief 并对 SAMPLE_BIND 跑命令。")
    return backup_root


def main() -> int:
    ap = argparse.ArgumentParser(description="Install 4.6 overlay onto grok-build")
    ap.add_argument("--src", help="grok-build-main 源码根目录")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-build", action="store_true", help="只拷文件和 bake，不 cargo build")
    ap.add_argument("--restore", metavar="BACKUP_DIR", help="从 backups/<stamp> 还原")
    args = ap.parse_args()
    try:
        if args.restore:
            restore(Path(args.restore).expanduser().resolve(), dry=args.dry_run)
            return 0
        src = find_src(args.src)
        install(src, dry=args.dry_run, no_build=args.no_build)
        return 0
    except InstallError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
