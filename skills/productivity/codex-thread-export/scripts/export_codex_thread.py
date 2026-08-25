#!/usr/bin/env python3
"""List and export locally stored Codex user/assistant messages."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
import time
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
                           {first_user_expr}, {updated_expr}, {cwd_expr}, {project_id_expr}
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
            }
            previous = threads.get(thread_id)
            if previous is None or (item["updated_at"] or 0) > (previous["updated_at"] or 0):
                threads[thread_id] = item
    return sorted(threads.values(), key=lambda item: item["updated_at"] or 0, reverse=True)


def extract_text(item_type: str, item: dict[str, Any]) -> str | None:
    if item_type == "agentMessage":
        text = item.get("text")
        return text if isinstance(text, str) else None
    if item_type == "userMessage":
        parts = item.get("content", [])
        if not isinstance(parts, list):
            return None
        return "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict)
            and part.get("type") == "text"
            and isinstance(part.get("text"), str)
        )
    return None


def export_thread(thread_id: str, history_databases: list[Path]) -> dict[str, Any] | None:
    for db_path in history_databases:
        try:
            with sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True) as conn:
                available = columns(conn, "thread_items")
                required = {"thread_id", "item_type", "item_json"}
                if not required.issubset(available):
                    continue
                order = "created_at_ms, rollout_ordinal" if {"created_at_ms", "rollout_ordinal"}.issubset(available) else "rowid"
                rows = conn.execute(
                    f"""
                    SELECT item_type, item_json
                    FROM thread_items
                    WHERE thread_id = ?
                      AND item_type IN ('userMessage', 'agentMessage')
                    ORDER BY {order}
                    """,
                    (thread_id,),
                ).fetchall()
        except sqlite3.Error:
            continue

        if not rows:
            continue
        messages: list[dict[str, str]] = []
        for item_type, item_json in rows:
            try:
                text = extract_text(item_type, json.loads(item_json))
            except (TypeError, json.JSONDecodeError):
                continue
            if text is not None:
                messages.append({item_type: text})
        return {"messages": messages}
    return None


def export_thread_with_retry(
    thread_id: str,
    history_databases: list[Path],
    wait_seconds: float,
    retry_interval: float,
) -> dict[str, Any] | None:
    deadline = time.monotonic() + wait_seconds
    exported = export_thread(thread_id, history_databases)
    while exported is None and time.monotonic() < deadline:
        time.sleep(min(retry_interval, max(0, deadline - time.monotonic())))
        exported = export_thread(thread_id, history_databases)
    return exported


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
    parser.add_argument("--history-db", type=Path, action="append", default=[])
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
    export_parser.add_argument(
        "--wait-seconds",
        type=float,
        default=10,
        help="Wait for recent messages to be projected to the history database.",
    )
    export_parser.add_argument(
        "--retry-interval",
        type=float,
        default=1,
        help="Seconds between history-database retries.",
    )
    args = parser.parse_args()
    selected_workspace = args.workspace if args.workspace is not None else parser.get_default("workspace")
    show_all_workspaces = args.all_workspaces or parser.get_default("all_workspaces")

    codex_home = args.codex_home.expanduser()
    if not codex_home.is_dir():
        print(f"Codex home does not exist: {codex_home}", file=sys.stderr)
        return 2

    state_dbs = args.state_db or discover_databases(codex_home, "threads")
    history_dbs = args.history_db or discover_databases(codex_home, "thread_items")
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
        thread_id = selected["thread_id"]
    elif args.thread_id:
        thread_id = args.thread_id
    else:
        print("请提供 --index <编号> 或 thread_id", file=sys.stderr)
        return 2

    if args.wait_seconds < 0 or args.retry_interval <= 0:
        print("--wait-seconds 必须不小于 0，--retry-interval 必须大于 0", file=sys.stderr)
        return 2
    exported = export_thread_with_retry(
        thread_id,
        history_dbs,
        args.wait_seconds,
        args.retry_interval,
    )
    if exported is None:
        if args.wait_seconds:
            print(
                f"等待 {args.wait_seconds:g} 秒后仍未找到该会话的用户消息或助手消息；"
                "该任务可能仍在同步到历史数据库，预计再等约 10 秒后可重试。",
                file=sys.stderr,
            )
        else:
            print("没有找到该会话的用户消息或助手消息", file=sys.stderr)
        return 1
    write_json(exported, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
