# Agent Engineer

> 企业级 AI Agent 开发资产统一管理仓库，涵盖 Skills、MCP 服务与各类工具。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 定位

本仓库是 AI Agent 工程化实践的核心资产库，致力于：

- **标准化** — 统一 Skill、MCP Server、工具脚本的开发与交付规范
- **可复用** — 提供开箱即用的模板与示例，降低重复建设成本
- **可维护** — 通过索引表、元数据与自动化校验保证资产质量

---

## 目录导航

| 目录 | 说明 |
|------|------|
| [`docs/`](./docs/) | 架构设计、命名规范、新手上手指南 |
| [`skills/`](./skills/) | 可被 Agent 加载的能力单元（Skill 集合） |
| [`mcp/`](./mcp/) | MCP Server 实现与客户端配置片段 |
| [`tools/`](./tools/) | 独立脚本、提示词模板、多步工作流 |
| [`examples/`](./examples/) | 端到端使用示例 |
| [`tests/`](./tests/) | 目录结构与元数据完整性校验 |

---

## 快速开始

### 1. 克隆仓库

```bash
git clone <repo-url>
cd agent-engineer
```

### 2. 运行结构校验

```bash
python tests/validate_structure.py
```

### 3. 新增 Skill

```bash
cp -r skills/_template skills/<category>/<your-skill-name>
# 编辑 SKILL.md，填写元数据与使用说明
```

### 4. 新增 MCP Server

```bash
cp -r mcp/_template mcp/servers/<your-server-name>
# 选择 Python 或 Node 模板，实现业务逻辑
```

---

## 贡献方式

请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解提交流程、审核标准与代码规范。

---

## 许可证

本项目采用 [MIT License](./LICENSE)。
