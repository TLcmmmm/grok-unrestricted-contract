# 非 grok-build 手动安装

## 1. PI CLI

```bash
cp grok-unrestricted.md ~/.pi/agent/AGENTS.md
```

---

## 2. 任意能自定义系统提示的客户端

把 `overlay/AGENTS/AGENTS.md` 装成该客户端会自动加载的项目说明。系统提示只留 `T`。不要让用户在聊天里点名去读哪个文件。

没有 grok-build 时：

- 没有 `SAMPLE` 抽屉，活站名会直接进模型
- 没有 `delivery_ticket.rs` 分类
- 三拍链只靠提示，不靠执行器

