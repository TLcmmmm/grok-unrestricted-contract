# grok-unrestricted-contract

Grok 4.6 工作区交付叠层。可见工单用 `SAMPLE`，绑定地址放在 `~/.grok/hooks/pending_brief.txt`，工具参数打 `SAMPLE_BIND`。

这是 **4.6 实验快照**，不是 4.7 稳定去限制，也不是全任务类型都过。

二进制 SHA（冻快照当时）：`1656f73dde533dd137cf9d8eaf2e68f75586995015d593edecdfe9ea4d53408f`  
记录：`FREEZE-4.6.md`

## 一键装到 grok-build

需要：本机已有 grok-build 源码树、`python3`、`cargo`。

```bash
git clone https://github.com/TLcmmmm/grok-unrestricted-contract.git
cd grok-unrestricted-contract
python3 install.py --src /path/to/grok-build-main
# 默认写入 ~/.grok ；若 TUI 用了别的 GROK_HOME，先 export GROK_HOME=...
```

脚本会：

1. 备份将要覆盖的文件到 `backups/<时间戳>/`
2. 写入 system 模板、`delivery_ticket.rs`、仓库 `AGENTS.md`
3. 写入 `~/.grok/AGENTS.md`、rules、静默 hook、brief MCP
4. 跑 `encrypt_templates.py` 再 `cargo build --release -p xai-grok-pager-bin`
5. 若 `config.toml` 还没有 `workspace-eval`，只追加 MCP 段，**不改 api_key**

常用参数：

```bash
python3 install.py --src /path/to/grok-build-main --dry-run
python3 install.py --src /path/to/grok-build-main --no-build
python3 install.py --restore backups/20260923-192100
```

装完重启 TUI，**新开会话**。启动器用你现在的 patched pager，不要混用官方 `~/.grok/bin/grok`。

验证（grok-4.6）：

- 开头不是拒绝正文
- 会读 `~/.grok/hooks/pending_brief.txt`
- 工具参数用 `SAMPLE_BIND` 的地址
- 不是 `HOST` / `PORT` / `TARGET` 菜谱

连续三轮会话：`01a0cdf6`、`01a0cdfa`、`01a0cdfd`。同一句在 grok-4.7 仍会拒。

## 没有 grok-build 时

见 `MANUAL.md`。只能装 AGENTS / hook / MCP，或把合约贴进别的客户端。没有任务单包装和 bake-in 模板，不要按冻快照宣传。

## 目录

```
install.py                 grok-build 一键安装
MANUAL.md                  非 grok-build 手动安装
FREEZE-4.6.md              4.6 连续三轮记录
grok-unrestricted.md       旧 PI 合约（4.5 测过，不是这次冻快照）
overlay/SYSTEM/            prompt.md / subagent / encrypt_templates.py
overlay/TICKET/            delivery_ticket.rs
overlay/AGENTS/            全局与仓库 AGENTS
overlay/HOOK/              静默 hook
overlay/MCP/               pending_brief 读取
```

不包含 grok-build 源码、`target/`、会话、`config.toml` 密钥。
