# Skills 索引

可被 Agent 直接加载的能力单元集合。每个 Skill 存放在 `<category>/<skill-name>/` 下，入口文件为 `SKILL.md`。

---

## 索引表

| 名称 | 分类 | 简介 | 状态 | 维护者 |
|------|------|------|------|--------|
| [codex-thread-export](./productivity/codex-thread-export/SKILL.md) | productivity | 导出本地 Codex 会话的用户与助手消息为 JSON | active | — |

---

## 分类说明

| 目录 | 适用场景 |
|------|----------|
| `coding/` | 代码生成、重构、审查、调试 |
| `writing/` | 文案撰写、润色、翻译、摘要 |
| `research/` | 信息检索、文献调研、竞品分析 |
| `data/` | 数据清洗、转换、分析、可视化 |
| `productivity/` | 开发效率工具、自动化流程 |

---

## 新增 Skill

```bash
cp -r skills/_template skills/<category>/<skill-name>
```

填写 `SKILL.md` 后在上方索引表中添加一行，并运行：

```bash
python tests/validate_structure.py
```
