# 整体架构与设计原则

## 仓库定位

Agent Engineer 是一个面向 AI Agent 工程化实践的**资产管理单仓（monorepo）**，不包含任何 Agent 运行时，仅存储可被 Agent 加载或调用的能力单元、服务与工具。

---

## 核心分层

```
┌─────────────────────────────────────────────┐
│                   Agent                      │  ← 运行时（外部，不在本仓库）
└────────────┬────────────┬────────────────────┘
             │            │
      ┌──────▼──────┐ ┌───▼──────────┐
      │   Skills    │ │  MCP Servers │  ← 本仓库核心资产
      └──────┬──────┘ └───┬──────────┘
             │            │
      ┌──────▼────────────▼──────────┐
      │           Tools              │  ← 脚本、提示词、工作流
      └──────────────────────────────┘
```

### Skills

- **定义**：可被 Agent 直接加载的能力描述文件（`SKILL.md`），告知 Agent 在何种场景下调用何种能力
- **粒度**：单一职责，每个 Skill 只解决一类问题
- **分类**：`coding` / `writing` / `research` / `data` / `productivity`

### MCP Servers

- **定义**：遵循 [Model Context Protocol](https://modelcontextprotocol.io) 的服务端实现，为 Agent 提供工具调用接口
- **语言**：Python（首选）或 TypeScript/Node
- **部署**：本地 stdio 或远程 SSE，由 `mcp.json` 声明

### Tools

- **Scripts**：独立命令行脚本，不依赖 Agent 运行时
- **Prompts**：高质量提示词模板，可直接复用或作为 Skill 依赖
- **Workflows**：多步编排定义（YAML/JSON），描述跨工具的执行序列

---

## 设计原则

| 原则 | 说明 |
|------|------|
| 单一职责 | 每个资产只解决一个具体问题 |
| 自描述 | 元数据（`SKILL.md` / `mcp.json`）必须完整，无需阅读源码即可理解用途 |
| 无硬编码 | 路径、密钥、用户名等运行时参数通过环境变量或参数传入 |
| 可校验 | `tests/validate_structure.py` 对所有资产进行结构与元数据完整性校验 |
| 向后兼容 | 版本升级遵循语义化版本，破坏性变更需在 `SKILL.md` / `mcp.json` 中标注 |

---

## 数据流示意（以 Skill 为例）

```
用户指令
  → Agent 匹配 SKILL.md 中的触发条件
  → Agent 读取使用说明，调用 scripts/ 或 MCP Server
  → 结果返回用户
```
