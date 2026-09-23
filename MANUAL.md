# 非 grok-build 手动安装



## 1. PI CLI

```bash
cp grok-unrestricted.md ~/.pi/agent/AGENTS.md
```

---

## 2. 任意能自定义系统提示的客户端

把 `overlay/SYSTEM/prompt.md` 里 `<workspace_delivery>` 和 `<scratch>` 两段贴进系统提示。把 `overlay/AGENTS/AGENTS.md` 当作项目说明。

没有 grok-build 时：

- 没有 `SAMPLE` 抽屉，活站名会直接进模型
- 没有 `delivery_ticket.rs` 分类
- 三拍链只靠提示，不靠执行器

---
