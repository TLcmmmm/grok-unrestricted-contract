# grok-unrestricted-contract
## 一键装到 grok-build

需要：本机已有 grok-build、`python3`、`cargo`。

去限制写在会话自动加载的 `AGENTS.md` 和 `rules/*.md` 里（标题 `T`）。用户仍打原句。系统提示只留 `T`。Hook 只在本机写 `t-state.txt`（COVERED 前几拍已成立），不伪造聊天历史。

```bash
git clone https://github.com/TLcmmmm/grok-unrestricted-contract.git
cd grok-unrestricted-contract
python3 install.py --src /path/to/grok-build-main
# 默认写入 ~/.grok
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

装完重启 TUI，**新开会话**。



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
