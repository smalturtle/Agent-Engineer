"""
validate_structure.py — 目录结构与元数据完整性校验脚本

用法：
    python tests/validate_structure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

ERRORS: list[str] = []


def err(msg: str) -> None:
    ERRORS.append(msg)


# ── 顶层必要文件 ────────────────────────────────────────────────────────────

def check_root_files() -> None:
    required = ["README.md", "CONTRIBUTING.md", "LICENSE", ".gitignore", ".cursorrules"]
    for f in required:
        if not (ROOT / f).is_file():
            err(f"[root] 缺少必要文件: {f}")


# ── docs/ ───────────────────────────────────────────────────────────────────

def check_docs() -> None:
    required = ["architecture.md", "conventions.md", "getting-started.md"]
    for f in required:
        if not (ROOT / "docs" / f).is_file():
            err(f"[docs] 缺少文件: docs/{f}")


# ── skills/ ─────────────────────────────────────────────────────────────────

SKILL_CATEGORIES = {"coding", "writing", "research", "data", "productivity"}
SKILL_REQUIRED_FRONT_MATTER = {"name", "description", "category", "version", "maintainer", "status"}


def parse_front_matter(path: Path) -> dict[str, str]:
    """极简 YAML Front Matter 解析（仅处理 key: value 形式）。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"')
    return meta


def check_skills() -> None:
    skills_dir = ROOT / "skills"

    if not (skills_dir / "README.md").is_file():
        err("[skills] 缺少 skills/README.md 索引文件")

    template_skill = skills_dir / "_template" / "SKILL.md"
    if not template_skill.is_file():
        err("[skills] 缺少 skills/_template/SKILL.md 模板文件")

    for category in SKILL_CATEGORIES:
        cat_dir = skills_dir / category
        if not cat_dir.is_dir():
            err(f"[skills] 缺少分类目录: skills/{category}/")

    for skill_dir in skills_dir.iterdir():
        if skill_dir.name.startswith("_") or not skill_dir.is_dir():
            continue
        if skill_dir.name not in SKILL_CATEGORIES:
            err(f"[skills] 未知分类目录: skills/{skill_dir.name}/（允许值: {sorted(SKILL_CATEGORIES)}）")
            continue
        for sub in skill_dir.iterdir():
            if not sub.is_dir():
                continue
            skill_md = sub / "SKILL.md"
            if not skill_md.is_file():
                err(f"[skills] {sub.relative_to(ROOT)} 缺少 SKILL.md")
                continue
            meta = parse_front_matter(skill_md)
            for field in SKILL_REQUIRED_FRONT_MATTER:
                if field not in meta or not meta[field] or meta[field].startswith("<"):
                    err(f"[skills] {sub.relative_to(ROOT)}/SKILL.md 元数据字段未填写或为占位符: {field}")
            if "category" in meta and meta["category"] not in SKILL_CATEGORIES:
                err(f"[skills] {sub.relative_to(ROOT)}/SKILL.md category 值无效: {meta['category']}")


# ── mcp/ ────────────────────────────────────────────────────────────────────

MCP_JSON_REQUIRED = {"name", "version", "description", "protocol_version", "entry", "maintainer", "status"}


def check_mcp() -> None:
    import json

    mcp_dir = ROOT / "mcp"

    if not (mcp_dir / "README.md").is_file():
        err("[mcp] 缺少 mcp/README.md 索引文件")

    template_dir = mcp_dir / "_template"
    for f in ["server.py", "index.ts", "mcp.json", "README.md"]:
        if not (template_dir / f).is_file():
            err(f"[mcp] 缺少模板文件: mcp/_template/{f}")

    servers_dir = mcp_dir / "servers"
    if not servers_dir.is_dir():
        err("[mcp] 缺少 mcp/servers/ 目录")
        return

    for server_dir in servers_dir.iterdir():
        if not server_dir.is_dir():
            continue
        mcp_json = server_dir / "mcp.json"
        if not mcp_json.is_file():
            err(f"[mcp] {server_dir.relative_to(ROOT)} 缺少 mcp.json")
            continue
        try:
            data = json.loads(mcp_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(f"[mcp] {mcp_json.relative_to(ROOT)} JSON 格式错误: {e}")
            continue
        for field in MCP_JSON_REQUIRED:
            if field not in data or not data[field] or str(data[field]).startswith("<"):
                err(f"[mcp] {mcp_json.relative_to(ROOT)} 字段未填写或为占位符: {field}")

        if not (server_dir / "README.md").is_file():
            err(f"[mcp] {server_dir.relative_to(ROOT)} 缺少 README.md")


# ── tools/ ──────────────────────────────────────────────────────────────────

def check_tools() -> None:
    tools_dir = ROOT / "tools"
    if not (tools_dir / "README.md").is_file():
        err("[tools] 缺少 tools/README.md 索引文件")
    for sub in ["scripts", "prompts", "workflows"]:
        if not (tools_dir / sub).is_dir():
            err(f"[tools] 缺少目录: tools/{sub}/")


# ── examples/ ───────────────────────────────────────────────────────────────

def check_examples() -> None:
    if not (ROOT / "examples" / "README.md").is_file():
        err("[examples] 缺少 examples/README.md 索引文件")


# ── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    check_root_files()
    check_docs()
    check_skills()
    check_mcp()
    check_tools()
    check_examples()

    if ERRORS:
        print(f"\n❌ 校验失败，发现 {len(ERRORS)} 个问题：\n")
        for e in ERRORS:
            print(f"  • {e}")
        print()
        sys.exit(1)
    else:
        print("\n✅ All checks passed.\n")


if __name__ == "__main__":
    main()
