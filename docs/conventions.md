# 命名规范、元数据格式与版本管理约定

## 命名规范

### 目录与文件名

| 类型 | 规则 | 示例 |
|------|------|------|
| 目录 | kebab-case，全小写 | `codex-thread-export/` |
| Markdown 文档 | SCREAMING_SNAKE_CASE（特殊文件）或 kebab-case | `SKILL.md`、`getting-started.md` |
| Python 文件 | snake_case | `export_codex_thread.py` |
| TypeScript/JS 文件 | camelCase 或 kebab-case | `mcpServer.ts`、`mcp-server.ts` |
| YAML/JSON 配置 | kebab-case | `mcp-config.json`、`openai.yaml` |

**禁止**：空格、中文、大写字母（SKILL.md / README.md / CONTRIBUTING.md 等约定文件除外）

---

## SKILL.md 元数据格式

每个 Skill 的 `SKILL.md` 必须以 YAML Front Matter 开头：

```yaml
---
name: <skill-name>                          # 与目录名一致，kebab-case
description: "<触发场景的一句话描述>"
category: <coding|writing|research|data|productivity>
version: "1.0.0"                            # 语义化版本
maintainer: <name-or-github-handle>
status: <active|experimental|deprecated>
tags: [tag1, tag2]                          # 可选，用于检索
requires: []                                # 可选，依赖的其他 Skill 或工具
---
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 唯一标识符，与目录名完全一致 |
| `description` | ✅ | 一句话，说明 Agent 应在何时使用此 Skill |
| `category` | ✅ | 五选一，决定存放目录 |
| `version` | ✅ | 语义化版本 `MAJOR.MINOR.PATCH` |
| `maintainer` | ✅ | 至少一个维护者 |
| `status` | ✅ | 当前状态 |
| `tags` | ❌ | 辅助检索标签 |
| `requires` | ❌ | 运行前置依赖 |

---

## mcp.json 元数据格式

```json
{
  "name": "server-name",
  "version": "1.0.0",
  "description": "一句话说明此 MCP Server 的职责",
  "protocol_version": "2024-11-05",
  "entry": "server.py",
  "runtime": "python|node",
  "dependencies": {
    "python": ">=3.10",
    "packages": []
  },
  "maintainer": "name-or-handle",
  "status": "active|experimental|deprecated"
}
```

---

## 版本管理约定

遵循 [Semantic Versioning 2.0.0](https://semver.org/)：

| 变更类型 | 版本递增 | 示例 |
|----------|----------|------|
| 破坏性变更（接口不兼容） | MAJOR | `1.0.0` → `2.0.0` |
| 新增功能（向后兼容） | MINOR | `1.0.0` → `1.1.0` |
| 缺陷修复、文档优化 | PATCH | `1.0.0` → `1.0.1` |

**破坏性变更**需在 `SKILL.md` / `mcp.json` 的 `description` 或 Body 中显式说明迁移路径。

---

## 状态定义

| 状态 | 说明 |
|------|------|
| `active` | 生产可用，持续维护 |
| `experimental` | 功能验证阶段，接口可能变动 |
| `deprecated` | 已弃用，提供替代方案说明，保留 3 个月后移除 |
