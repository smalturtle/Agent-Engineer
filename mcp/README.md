# MCP Servers 索引

遵循 [Model Context Protocol](https://modelcontextprotocol.io) 的服务端实现集合。

---

## 索引表

| 名称 | 协议版本 | 语言 | 简介 | 状态 | 维护者 |
|------|----------|------|------|------|--------|
| — | — | — | 暂无已发布的 Server | — | — |

---

## 新增 MCP Server

```bash
cp -r mcp/_template mcp/servers/<server-name>
```

填写 `mcp.json` 和 `README.md` 后在上方索引表中添加一行，并运行：

```bash
python tests/validate_structure.py
```

---

## 客户端配置片段

`configs/` 目录存放可复用的客户端配置片段，按工具命名：

| 文件 | 适用客户端 |
|------|-----------|
| `configs/cursor.json` | Cursor IDE |
| `configs/claude-desktop.json` | Claude Desktop |
