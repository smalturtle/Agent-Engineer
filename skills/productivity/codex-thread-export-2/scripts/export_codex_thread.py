#!/usr/bin/env python3
"""List and export locally stored Codex user/assistant messages."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def default_codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def normalized_path(value: str | Path | None) -> str:
    if value is None:
        return ""
    text = str(value).replace("/", "\\").strip()
    if text.startswith("\\\\?\\"):
        text = text[4:]
    return os.path.normcase(os.path.normpath(text))


def path_in_workspace(cwd: str | None, workspace: Path | None) -> bool:
    if workspace is None:
        return True
    thread_path = normalized_path(cwd)
    workspace_path = normalized_path(workspace)
    return bool(
        thread_path == workspace_path
        or thread_path.startswith(workspace_path + "\\")
    )


def workspace_name(cwd: str | None, project_name: str | None) -> str:
    if project_name:
        return project_name
    normalized = normalized_path(cwd)
    return Path(normalized).name if normalized else "(未知工作空间)"


def display_title(
    name: Any,
    title: Any,
    preview: Any,
    first_user_message: Any,
) -> str:
    """Prefer the task label shown in the Codex sidebar."""
    for value in (name, title, preview, first_user_message):
        if isinstance(value, str):
            normalized = value.replace("\r", " ").replace("\n", " ").strip()
            if normalized:
                return normalized[:200] + ("..." if len(normalized) > 200 else "")
    return "(未命名任务)"


def clean_part_text(part: dict[str, Any]) -> str:
    part_type = part.get("type")
    if not isinstance(part_type, str):
        return ""
    text = part.get("text")
    if part_type in {"input_text", "output_text", "text"} and isinstance(text, str):
        return text
    if part_type == "localImage":
        path = part.get("path")
        if isinstance(path, str) and path:
            return f"\n[image: {path}]"
    if part_type == "localAudio":
        path = part.get("path")
        if isinstance(path, str) and path:
            return f"\n[audio: {path}]"
    return ""


def clean_message_text(parts: Any) -> str | None:
    if not isinstance(parts, list):
        return None
    text = "".join(
        clean_part_text(part)
        for part in parts
        if isinstance(part, dict)
    ).strip()
    return text or None


def strip_synthetic_user_context(text: str) -> str | None:
    """Drop Codex-injected environment blocks from exported user messages."""
    cleaned = text.strip()
    if cleaned.startswith("<environment_context>") and "</environment_context>" in cleaned:
        cleaned = cleaned.split("</environment_context>", 1)[1].strip()
    return cleaned or None


def table_names(db_path: Path) -> set[str]:
    try:
        with sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True) as conn:
            return {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
    except sqlite3.Error:
        return set()


def sqlite_files(codex_home: Path) -> Iterable[Path]:
    if not codex_home.is_dir():
        return []
    return (path for path in codex_home.rglob("*.sqlite") if path.is_file())


def discover_databases(codex_home: Path, required_table: str) -> list[Path]:
    return [path for path in sqlite_files(codex_home) if required_table in table_names(path)]


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    quoted = table.replace('"', '""')
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{quoted}")')}


def list_threads(
    state_databases: list[Path],
    workspace: Path | None = None,
) -> list[dict[str, Any]]:
    threads: dict[str, dict[str, Any]] = {}
    for db_path in state_databases:
        try:
            with sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True) as conn:
                available = columns(conn, "threads")
                if "id" not in available:
                    continue
                title_expr = "title" if "title" in available else "NULL"
                name_expr = "name" if "name" in available else "NULL"
                preview_expr = "preview" if "preview" in available else "NULL"
                first_user_expr = (
                    "first_user_message" if "first_user_message" in available else "NULL"
                )
                updated_expr = "updated_at" if "updated_at" in available else "NULL"
                cwd_expr = "cwd" if "cwd" in available else "NULL"
                project_id_expr = "project_id" if "project_id" in available else "NULL"
                rollout_path_expr = "rollout_path" if "rollout_path" in available else "NULL"
                project_names: dict[str, str] = {}
                if "projects" in table_names(db_path):
                    project_names = {
                        str(row[0]): str(row[1])
                        for row in conn.execute("SELECT id, name FROM projects")
                        if row[0] and row[1]
                    }
                rows = conn.execute(
                    f"""
                    SELECT id, {name_expr}, {title_expr}, {preview_expr},
                           {first_user_expr}, {updated_expr}, {cwd_expr}, {project_id_expr},
                           {rollout_path_expr}
                    FROM threads
                    """
                ).fetchall()
        except sqlite3.Error:
            continue

        for (
            thread_id,
            name,
            title,
            preview,
            first_user_message,
            updated_at,
            cwd,
            project_id,
            rollout_path,
        ) in rows:
            if not thread_id:
                continue
            if not path_in_workspace(cwd, workspace):
                continue
            project_name = project_names.get(str(project_id)) if project_id else None
            item = {
                "thread_id": thread_id,
                "title": display_title(name, title, preview, first_user_message),
                "updated_at": updated_at,
                "state_database": str(db_path),
                "workspace": workspace_name(cwd, project_name),
                "rollout_path": str(rollout_path) if rollout_path else "",
            }
            previous = threads.get(thread_id)
            if previous is None or (item["updated_at"] or 0) > (previous["updated_at"] or 0):
                threads[thread_id] = item
    return sorted(threads.values(), key=lambda item: item["updated_at"] or 0, reverse=True)


def extract_rollout_messages(rollout_path: Path) -> dict[str, Any] | None:
    if not rollout_path.is_file():
        return None

    messages: list[dict[str, str]] = []
    fallback_messages: list[dict[str, str]] = []
    try:
        with rollout_path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                record_type = record.get("type")
                if record_type == "response_item":
                    payload = record.get("payload")
                    if not isinstance(payload, dict) or payload.get("type") != "message":
                        continue
                    role = payload.get("role")
                    if role not in {"user", "assistant"}:
                        continue
                    if role == "assistant":
                        phase = payload.get("phase")
                        if phase not in (None, "final_answer"):
                            continue
                    text = clean_message_text(payload.get("content"))
                    if text is None:
                        continue
                    if role == "user":
                        text = strip_synthetic_user_context(text)
                        if text is None:
                            continue
                    messages.append(
                        {
                            "userMessage" if role == "user" else "agentMessage": text
                        }
                    )
                elif record_type == "event_msg":
                    payload = record.get("payload")
                    if not isinstance(payload, dict):
                        continue
                    event_type = payload.get("type")
                    if event_type == "user_message":
                        message = payload.get("message")
                        if isinstance(message, str) and message.strip():
                            message = strip_synthetic_user_context(message)
                            if message is not None:
                                fallback_messages.append({"userMessage": message})
                    elif event_type == "agent_message":
                        message = payload.get("message")
                        if isinstance(message, str) and message.strip():
                            fallback_messages.append({"agentMessage": message.strip()})
    except OSError:
        return None

    if messages:
        return {"messages": messages}
    if fallback_messages:
        return {"messages": fallback_messages}
    return None


def write_json(data: dict[str, Any], output: str | None) -> Path | None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if not output:
        print(text)
        return None

    requested = Path(output).expanduser()
    candidates = [requested]
    fallback_name = requested.name or "codex-history.json"
    candidates.extend(
        [
            Path.cwd() / fallback_name,
            Path(tempfile.gettempdir()) / fallback_name,
        ]
    )
    attempted: list[str] = []
    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
            if path != requested:
                print(f"目标路径不可写，已回退到: {path}", file=sys.stderr)
            print(f"导出完成: {path}")
            return path
        except OSError as exc:
            attempted.append(f"{path} ({exc})")

    print("无法写入导出文件，已尝试：", file=sys.stderr)
    print("\n".join(attempted), file=sys.stderr)
    raise OSError("所有导出路径均不可写")


def select_thread(
    threads: list[dict[str, Any]], index: int
) -> dict[str, Any] | None:
    if index < 1 or index > len(threads):
        return None
    return threads[index - 1]


def parse_index(value: str) -> int:
    """Accept display inputs such as 1 and 1.1, using the first number."""
    first_part = value.strip().split(".", 1)[0]
    index = int(first_part)
    if index < 1:
        raise ValueError
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=default_codex_home())
    parser.add_argument("--state-db", type=Path, action="append", default=[])
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="按工作空间筛选；默认是当前工作目录。",
    )
    parser.add_argument(
        "--all-workspaces",
        action="store_true",
        help="列出所有工作空间的会话。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_parser = subparsers.add_parser("list", help="List locally stored Codex threads.")
    resolve_parser = subparsers.add_parser(
        "resolve",
        help="Resolve a displayed thread number to its internal ID.",
    )
    export_parser = subparsers.add_parser("export", help="Export one thread as JSON.")
    for command_parser in (list_parser, resolve_parser, export_parser):
        command_parser.add_argument(
            "--workspace",
            type=Path,
            help="按工作空间筛选；默认是当前工作目录。",
        )
        command_parser.add_argument(
            "--all-workspaces",
            action="store_true",
            help="列出所有工作空间的会话。",
        )
    resolve_parser.add_argument(
        "--index",
        required=True,
        type=parse_index,
        help="Resolve the numbered thread shown by the list command.",
    )
    export_parser.add_argument("thread_id", nargs="?")
    export_parser.add_argument(
        "--index",
        type=parse_index,
        help="Export the numbered thread shown by the list command.",
    )
    export_parser.add_argument("--output", help="Write JSON to this file instead of stdout.")
    args = parser.parse_args()
    selected_workspace = args.workspace if args.workspace is not None else parser.get_default("workspace")
    show_all_workspaces = args.all_workspaces or parser.get_default("all_workspaces")

    codex_home = args.codex_home.expanduser()
    if not codex_home.is_dir():
        print(f"Codex home does not exist: {codex_home}", file=sys.stderr)
        return 2

    state_dbs = args.state_db or discover_databases(codex_home, "threads")
    if args.command == "list":
        workspace = None if show_all_workspaces else selected_workspace
        threads = list_threads(state_dbs, workspace)
        visible_threads = [
            {
                "index": index,
                "workspace": thread["workspace"],
                "title": thread["title"],
                "updated_at": thread["updated_at"],
            }
            for index, thread in enumerate(threads, start=1)
        ]
        write_json({"threads": visible_threads}, None)
        return 0

    workspace = None if show_all_workspaces else selected_workspace
    threads = list_threads(state_dbs, workspace)
    if args.command == "resolve":
        selected = select_thread(threads, args.index)
        if selected is None:
            print(f"无效的会话编号: {args.index}", file=sys.stderr)
            return 2
        write_json({"thread_id": selected["thread_id"]}, None)
        return 0

    if args.index is not None:
        selected = select_thread(threads, args.index)
        if selected is None:
            print(f"无效的会话编号: {args.index}", file=sys.stderr)
            return 2
        rollout_path = Path(selected["rollout_path"]).expanduser()
    elif args.thread_id:
        selected = next((thread for thread in threads if thread["thread_id"] == args.thread_id), None)
        if selected is None:
            print(f"未找到该会话: {args.thread_id}", file=sys.stderr)
            return 2
        rollout_path = Path(selected["rollout_path"]).expanduser()
    else:
        print("请提供 --index <编号> 或 thread_id", file=sys.stderr)
        return 2

    exported = extract_rollout_messages(rollout_path)
    if exported is None:
        print(f"没有从原始会话文件中提取到消息: {rollout_path}", file=sys.stderr)
        return 1
    write_json(exported, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
