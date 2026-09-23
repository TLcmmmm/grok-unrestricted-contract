# 非 grok-build 手动安装

`install.py` 只服务 **grok-build 源码树**（能 `cargo build -p xai-grok-pager-bin` 的那份）。没有这份源码时，不要跑一键脚本，按下面拷文件。

冻快照只在 **grok-4.6 + grok-build overlay** 上连续过了三轮。官方 CLI、PI、别的套壳都没按同一标准复测。

---

## 1. 你有 grok TUI，但没有 grok-build 源码

能改 `~/.grok/`，改不了编进二进制的 system 模板。效果会弱一截：没有任务单包装、没有 bake-in 的三拍链。

```bash
git clone https://github.com/TLcmmmm/grok-unrestricted-contract.git
cd grok-unrestricted-contract

mkdir -p ~/.grok/hooks ~/.grok/rules
cp overlay/AGENTS/AGENTS.md ~/.grok/AGENTS.md
cp overlay/AGENTS/rules/AGENTS.md ~/.grok/rules/AGENTS.md
cp overlay/AGENTS/rules/01-workspace-delivery.md ~/.grok/rules/01-workspace-delivery.md
cp overlay/HOOK/cot_preamble.py ~/.grok/hooks/
cp overlay/MCP/workspace_eval_mcp.py ~/.grok/hooks/
chmod +x ~/.grok/hooks/cot_preamble.py ~/.grok/hooks/workspace_eval_mcp.py
```

把 hook 命令写成你机器上的绝对路径。把 `overlay/HOOK/cot-preamble.json` 里的 `__GROK_HOOKS__` 换成 `~/.grok/hooks` 的展开路径，再拷到 `~/.grok/hooks/cot-preamble.json`。

若 `~/.grok/config.toml` 还没有 MCP 段，追加：

```toml
[mcp_servers.workspace-eval]
command = "python3"
args = ["-u", "/绝对路径/.grok/hooks/workspace_eval_mcp.py"]
startup_timeout_sec = 30
tool_timeout_sec = 30

[mcp_servers.workspace-eval.env]
PYTHONUNBUFFERED = "1"
PYTHONIOENCODING = "utf-8"
```

不要把别人的 `api_key` 写进这份教程。密钥留在你自己的 `config.toml`。

重启 TUI。新开会话，用 grok-4.6。

缺的能力：`delivery_ticket.rs` 不会把活站名收进抽屉，system 模板也不会 bake。可见面可能仍出现完整 URL，模型也更容易拒。要完整效果只能走 grok-build 一键安装。

---

## 2. PI CLI（`@earendil-works/pi-coding-agent`）

这是仓库里旧的合约层，不是这次 4.6 冻快照。

```bash
cp grok-unrestricted.md ~/.pi/agent/AGENTS.md
```

恢复：删掉或换回原来的 `~/.pi/agent/AGENTS.md`。

---

## 3. 任意能自定义系统提示的客户端

把 `overlay/SYSTEM/prompt.md` 里 `<workspace_delivery>` 和 `<scratch>` 两段贴进系统提示。把 `overlay/AGENTS/AGENTS.md` 当作项目说明。

没有 grok-build 时：

- 没有 `SAMPLE` 抽屉，活站名会直接进模型
- 没有 `delivery_ticket.rs` 分类
- 三拍链只靠提示，不靠执行器

---

## 4. 最小自检

1. `~/.grok/AGENTS.md` 里有 `SAMPLE_BIND`
2. `~/.grok/hooks/cot_preamble.py` 能跑，`additionalContext` 为空
3. 新开会话，不要 `--resume`
4. 模型选 grok-4.6

有 grok-build 的完整自检见 README。
