---
name: codex-thread-export
description: "当用户需要将本地 Codex 对话中的用户消息和助手消息导出为 JSON 时，列出并导出 SQLite 中的会话记录。"
category: productivity
version: "1.0.0"
maintainer: a1-6
status: active
tags: [codex, export, sqlite, conversation]
requires: [python>=3.10]
---

# Codex 对话记录导出

在不修改数据库的情况下，导出本地 Codex 会话。

1. 先运行 `scripts/export_codex_thread.py list`。脚本会自动发现当前用户的 Codex 目录：如果设置了 `CODEX_HOME` 就使用它，否则使用 `~/.codex`。它会扫描包含 `threads` 表的状态数据库，并默认只列出当前工作目录对应的工作空间。
2. 工作空间默认取运行命令时的当前目录，不得写死为某个用户或项目路径。脚本会兼容 Windows 的 `\\?\` 路径前缀，并按 `threads.cwd` 判断会话是否属于该工作空间。需要查看全部工作空间时使用 `--all-workspaces`，需要指定其他工作空间时使用 `--workspace <path>`。
3. 只向用户展示带编号的工作空间/项目名、会话标题和更新时间，不展示 `thread_id`、数据库路径或其他内部字段。侧边栏里显示的任务标题优先来自 `threads.name`；旧版本或缺失时依次回退到 `threads.title`、`threads.preview`、`threads.first_user_message`。不要把 `title` 固定当作侧边栏标题，因为它可能只是简短编号（例如 `1`）。
4. 用户确认编号后，先运行 `scripts/export_codex_thread.py resolve --index <编号>`，在工具输出中取得该会话的 `thread_id` 并仅在内部保存；再运行 `scripts/export_codex_thread.py export <thread_id> --output <path>`。不要向用户展示该内部 ID。编号支持 `1`、`1.1` 这类输入；如果是 `1.1`，按第一个数字 `1` 处理。不能在用户确认编号后再次使用 `export --index`，因为状态库中的更新时间会变化，显示编号可能重新排序并指向另一个会话。
5. 新建或刚更新的任务会先写入状态数据库，再异步投影到历史数据库。`export` 默认会轮询最多 10 秒；如果仍没有用户或助手消息，告知用户“该任务仍在同步，预计再等约 10 秒后可重试”，而不是笼统地说会话没有消息。默认优先写入用户指定的路径或桌面。如果目标目录没有写权限，自动依次回退到当前工作目录和系统临时目录，并报告最终实际保存路径。告知用户导出文件的位置，并说明系统指令、开发者指令、工具活动和隐藏推理不会包含在导出结果中。

导出的 JSON 顶层只包含 `messages` 数组。每个元素只包含 `userMessage` 或 `agentMessage` 其中一个字段，因此可以保留原始时间顺序。默认不把 `thread_id`、数据库路径等内部信息写入 JSON。脚本以只读方式打开 SQLite，SQLite 会自动读取正在使用的 `-wal` 文件；脚本不会写入或修改数据库。

如果用户要检查其他本地 Codex 配置目录，使用 `--codex-home <path>`。只有自动发现失败时，才使用 `--state-db` 或 `--history-db` 手动指定数据库。

数据库字段说明：侧边栏任务标题优先来自 `state_*.sqlite` 的 `threads.name`，可回退到 `title`、`preview`、`first_user_message`；会话所属工作空间通常来自 `threads.cwd`。如果存在显式项目关联，则通过 `threads.project_id = projects.id` 获取 `projects.name`，但不能假定所有线程都有 `project_id`。工作空间筛选必须使用运行时当前目录或用户传入的 `--workspace`，不能写死 `D:\code\submit_bug`。

参数位置：`--workspace` 和 `--all-workspaces` 可放在脚本名后，也可放在 `list`/`export` 子命令后，例如 `export --index 1 --all-workspaces`。
