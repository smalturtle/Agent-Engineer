# <server-name>

> 一句话说明此 MCP Server 的职责。

---

## 安装

```bash
# Python
pip install -r requirements.txt

# Node
npm install
```

## 配置

复制环境变量模板并填写：

```bash
cp .env.example .env
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `EXAMPLE_VAR` | ✅ | 示例变量说明 |

## 运行

```bash
# Python（stdio）
python server.py

# Node（stdio）
npx ts-node index.ts
```

## 接入 Cursor

在 Cursor MCP 配置中添加：

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "python",
      "args": ["<absolute-path>/server.py"]
    }
  }
}
```

## 工具列表

| 工具名 | 说明 | 参数 |
|--------|------|------|
| `<tool-name>` | — | `<param>`: string |

## 开发说明

<!-- 架构说明、测试方式、已知限制等 -->
