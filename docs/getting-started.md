# 新用户快速上手指南

## 环境要求

| 工具 | 最低版本 |
|------|----------|
| Python | 3.10+ |
| Node.js | 20+ |
| Git | 2.40+ |

---

## 第一步：克隆仓库

```bash
git clone <repo-url>
cd agent-engineer
```

---

## 第二步：了解目录结构

```
agent-engineer/
├── skills/          # Agent 能力单元
│   ├── coding/      # 编程开发类
│   ├── writing/     # 写作润色类
│   ├── research/    # 调研检索类
│   ├── data/        # 数据处理类
│   └── productivity/# 效率工具类
├── mcp/             # MCP Server 实现
├── tools/           # 独立脚本与提示词
├── docs/            # 本文档所在目录
├── examples/        # 端到端使用示例
└── tests/           # 结构校验脚本
```

---

## 第三步：运行结构校验

验证仓库元数据完整性：

```bash
python tests/validate_structure.py
```

全部通过后输出：`✅ All checks passed.`

---

## 第四步：使用现有 Skill

每个 Skill 目录下的 `SKILL.md` 包含完整的触发条件和使用方式。以 `codex-thread-export` 为例：

```
skills/productivity/codex-thread-export/
├── SKILL.md                        # 阅读此文件了解用法
├── agents/openai.yaml              # Agent 配置
└── scripts/export_codex_thread.py  # 核心脚本
```

直接运行脚本：

```bash
python skills/productivity/codex-thread-export/scripts/export_codex_thread.py list
```

---

## 第五步：新增自己的 Skill

```bash
# 1. 从模板复制
cp -r skills/_template skills/<category>/<your-skill-name>

# 2. 编辑元数据（必填字段见 docs/conventions.md）
open skills/<category>/<your-skill-name>/SKILL.md

# 3. 在索引表中登记
open skills/README.md

# 4. 运行校验
python tests/validate_structure.py
```

---

## 第六步：新增 MCP Server

```bash
# 1. 从模板复制
cp -r mcp/_template mcp/servers/<your-server-name>

# 2. 选择实现语言并编辑入口文件
# Python: mcp/servers/<name>/server.py
# Node:   mcp/servers/<name>/index.ts

# 3. 填写 mcp.json 配置清单

# 4. 在索引表中登记
open mcp/README.md

# 5. 运行校验
python tests/validate_structure.py
```

---

## 更多资源

- [架构设计](./architecture.md)
- [命名与元数据规范](./conventions.md)
- [贡献指南](../CONTRIBUTING.md)
