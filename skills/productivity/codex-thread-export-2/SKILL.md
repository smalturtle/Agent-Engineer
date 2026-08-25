---
name: codex-thread-export
description: "导出本地 Codex 会话中的用户消息和助手消息为 JSON；适用于从 Codex 本地会话记录中提取对话时。"
metadata:
  short-description: 导出 Codex 本地会话为 JSON
---

# Codex 本地会话导出

目标：在不修改 SQLite 数据库的前提下，把本地 Codex 会话导出为只含 `messages` 数组的 JSON。

## 快速执行流程

### 1. 用户尚未提供编号

在运行时当前工作目录执行：

```powershell
python "<skill-dir>\scripts\export_codex_thread.py" list
```

其中 `<skill-dir>` 是本 skill 所在目录。不要把工作区路径写死。

将脚本返回的 JSON 转为可读清单后展示，至少包含：

```text
1. 主题（2026-08-25 16:27）
```
默认将所有历史记录展示出来
只展示编号、主题、更新时间；不要展示 `thread_id`、SQLite 路径等内部字段。
默认不突出显示 workspace，只有不同 workspace 中出现同名会话时才附加 workspace 以便区分。

时间戳转换规则：`updated_at` 是 Unix 秒，使用运行环境本地时区转换为 `YYYY-MM-DD HH:mm`。

### 2. 用户已提供编号

直接导出，不要先执行 `resolve`：

```powershell
python "<skill-dir>\scripts\export_codex_thread.py" export --index <编号> --output "<输出路径>"
```

编号处理：

- `11` 直接使用 `11`。
- `11.1` 按 `11` 处理。
- 无效编号直接报告脚本错误并停止。

默认输出路径：当前工作目录下的 `codex_thread_<编号>.json`。
如果用户指定了输出路径，优先使用用户路径。
脚本会在目标路径不可写时依次回退到当前工作目录、系统临时目录；最终回复必须报告实际写入路径。

### 3. 导出后校验

导出成功后快速读取 JSON，确认：

- 文件可解析；
- 顶层只有 `messages`；
- `messages` 是数组；
- 每条消息只含 `userMessage` 或 `agentMessage` 之一；
- 消息数组非空时报告条数；
- 消息为空或提取失败时明确报告，不自行扫描其他表。

## 会话范围

- 默认只列出运行时当前工作目录及其子目录中的会话。
- 其他范围使用 `--workspace <path>`。
- 全部 workspace 使用 `--all-workspaces`。
- `--workspace` 和 `--all-workspaces` 可放在脚本名后，也可放在 `list`、`resolve`、`export` 后。
- 用户要求检查其他 Codex 配置目录时使用 `--codex-home <path>`。
- 只有自动发现数据库失败时才使用 `--state-db <path>`；不要默认手动猜数据库路径。
- 支持 Windows `\\?\` 路径前缀。

示例：

```powershell
python "<skill-dir>\scripts\export_codex_thread.py" list --all-workspaces
python "<skill-dir>\scripts\export_codex_thread.py" export --index 1 --workspace "D:\other-project" --output "D:\out\thread.json"
python "<skill-dir>\scripts\export_codex_thread.py" list --codex-home "C:\Users\name\.codex"
```

## 标题与 workspace

列表标题按以下优先级取得：

1. `threads.name`
2. `title`
3. `preview`
4. `first_user_message`
5. `(未命名任务)`

workspace 标签不是独立数据库字段：

- 优先从 `threads.project_id -> projects.name` 派生；
- 否则从 `threads.cwd` 的目录名派生；
- 筛选始终使用运行时当前目录或用户传入的 `--workspace`，不能写死任何具体工作区。

## 正文提取规则

正文优先读取 `threads.rollout_path` 指向的原始 `.jsonl`，不使用 `thread_items`。

主消息标签：

- 用户：`type=response_item`、`payload.type=message`、`payload.role=user`，读取 `content[].type=input_text`。
- 助手：`type=response_item`、`payload.type=message`、`payload.role=assistant` 且 `phase=final_answer`，读取 `content[].type=output_text`。

过滤规则：

- 完整的 `<environment_context>...</environment_context>` 用户记录是 Codex 注入内容，整条丢弃。
- 如果环境块后还有用户文本，只保留结束标签之后的文本。
- 忽略 `developer`、`tool`、`reasoning`、`commentary`、`aborted`、`token_count` 等内容。
- 只有主标签完全没有消息时，才回退到 `event_msg` 的 `user_message` 和 `agent_message`。
- 回退的用户消息同样移除 environment context。
- 仍无消息时明确报告“没有从原始会话文件中提取到消息”，不要改查其他表。

导出格式示例：

```json
{
  "messages": [
    {"userMessage": "用户消息"},
    {"agentMessage": "助手消息"}
  ]
}
```

保持原始消息顺序。默认不写入 `thread_id`、数据库路径、workspace 等内部信息。
脚本只读 SQLite；正文来自原始 `.jsonl`，不会修改数据库。

## 执行注意点

- 用户给出编号后，不要再次列出会话，也不要额外执行 `resolve`。
- 不要要求用户提供 thread ID；编号已经足够。
- 不要把原始列表 JSON 原样甩给用户，必须转换成“编号 + 主题 + 时间”清单。
- 不要把 `<environment_context>` 内容导出到用户消息中。
- 不要为了补全内容而读取 `thread_items` 或其他数据库表。
- 输出成功后应检查消息数量；不要只依据“导出完成”字样判断成功。
- 文件名默认使用 `codex_thread_<编号>.json`，避免覆盖同一目录下的通用文件名。
