# 贡献指南

感谢你为 Agent Engineer 贡献内容！请在提交前仔细阅读本指南。

---

## 分支与提交规范

### 分支命名

```
feat/<scope>/<short-desc>    # 新增资产
fix/<scope>/<short-desc>     # 缺陷修复
docs/<short-desc>             # 文档变更
refactor/<scope>/<short-desc> # 重构
```

### Commit Message 格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

[可选 body]

[可选 footer]
```

常用 type：`feat` / `fix` / `docs` / `refactor` / `test` / `chore`

示例：
```
feat(skills/productivity): add codex-thread-export skill
fix(mcp/servers/sqlite): handle WAL mode read error
docs(getting-started): clarify Python version requirement
```

---

## 新增 Skill

1. 从模板复制：`cp -r skills/_template skills/<category>/<skill-name>`
2. 填写 `SKILL.md` 中所有必填元数据字段（`name`、`description`、`triggers`、`usage`）
3. 将 Skill 添加到 `skills/README.md` 索引表
4. 运行 `python tests/validate_structure.py` 确保校验通过
5. 发起 Pull Request，标题格式：`feat(skills/<category>): add <skill-name>`

---

## 新增 MCP Server

1. 从模板复制：`cp -r mcp/_template mcp/servers/<server-name>`
2. 选择 `server.py`（Python）或 `index.ts`（Node）实现业务逻辑
3. 完整填写 `mcp.json` 配置清单
4. 补充 `README.md`，包含安装、配置、运行步骤
5. 将 Server 添加到 `mcp/README.md` 索引表
6. 运行 `python tests/validate_structure.py` 确保校验通过
7. 发起 Pull Request

---

## 新增工具/脚本

1. 脚本放入 `tools/scripts/<lang>/`，提示词放入 `tools/prompts/<category>/`
2. 工作流定义放入 `tools/workflows/`
3. 在 `tools/README.md` 索引表中添加条目
4. 发起 Pull Request

---

## 审核标准

| 检查项 | 要求 |
|--------|------|
| 元数据完整性 | `SKILL.md` / `mcp.json` 必填字段均已填写 |
| 文档质量 | 使用示例清晰，无歧义 |
| 代码风格 | 遵循 `.cursorrules` 中定义的规范 |
| 无敏感信息 | 不包含密钥、密码、个人路径硬编码 |
| 校验通过 | `validate_structure.py` 无报错 |

---

## 行为准则

请保持尊重与建设性。所有贡献者均需遵守基本的开源社区行为准则。
