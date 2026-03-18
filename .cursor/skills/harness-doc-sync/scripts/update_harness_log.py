#!/usr/bin/env python3
"""Create one harness record per task, then conditionally align root harness docs."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

ROOT_AGENTS_SECTION_TITLE = "## 4. 任务收尾提醒（Harness 同步）"
ROOT_AGENTS_SECTION_BODY = (
    f"{ROOT_AGENTS_SECTION_TITLE}\n\n"
    "- 在 AI Coding 任务完成后，提醒用户使用 REPO Skill：`harness-doc-sync`。\n"
    "- 目标：按需同步 `AGENTS.md`、`ARCHITECTURE.md`、`TODO.md`，并生成 `docs/harness/records/<YYYYMMDD-HHMMSS>-<摘要>.md`。\n"
)

ROOT_ARCHITECTURE_SINK_NOTE = (
    "> 说明：根级架构文档只保留导航层（L0-L3）。"
    "实现细节应下沉到对应子项目文档（例如 `*/docs/architecture/`）。"
)

ROOT_TODO_SECTION_TITLE = "## P0：Harness 文档对齐（任务收尾）"
ROOT_TODO_SECTION_BODY = (
    f"{ROOT_TODO_SECTION_TITLE}\n\n"
    "- Intent：每次 AI Coding 完成后，同步根级工程入口与 Harness 记录目录，避免文档漂移。\n"
    "- Constraints：不放宽仓库级规则，不覆盖未完成任务的验收标准。\n"
    "- Tasks：\n"
    "  - 使用 `harness-doc-sync` 更新 `AGENTS.md`、`ARCHITECTURE.md`、`TODO.md`。\n"
    "  - 在 `docs/harness/records/` 生成 `YYYYMMDD-HHMMSS-摘要.md` 记录。\n"
    "- Checks：\n"
    "  - `rg \"任务收尾提醒（Harness 同步）\" AGENTS.md`\n"
    "  - `rg \"L0-L3\" ARCHITECTURE.md`\n"
    "  - `rg \"Harness 文档对齐\" TODO.md`\n"
    "- DoD：根级入口与记录目录同步完成，且记录文件可追溯本次变更。\n"
    "- Rollback：回退本次文档变更并删除新增记录文件。\n"
)
RECORD_TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


def run(cmd: List[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=str(cwd), check=True, text=True, capture_output=True)
    return result.stdout


def collect_changed_files(repo_root: Path) -> List[str]:
    output = run(["git", "status", "--short"], repo_root)
    files: List[str] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        payload = line[3:].strip()
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1].strip()
        files.append(payload)
    return sorted(set(files))


def infer_scope(path: str) -> str:
    if path.startswith(".agents/skills/"):
        return "harness-skill"
    if path.startswith("docs/"):
        return "docs"
    if path.startswith("src/"):
        return "source"
    if path.startswith("tests/"):
        return "tests"
    if path.endswith(".md"):
        return "docs"
    return "misc"


def sanitize_summary(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[\\/:*?\"<>|`]+", "", text)
    text = text.strip(".-")
    return text[:80] or "untitled"


def write_if_changed(path: Path, content: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if old == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def remove_section(content: str, title: str) -> str:
    return re.sub(
        rf"\n{re.escape(title)}\n[\s\S]*?(?=\n##\s|\Z)",
        "\n",
        content,
        flags=re.MULTILINE,
    )


def upsert_section(content: str, title: str, section_body: str) -> str:
    updated = remove_section(content, title)
    return updated.rstrip() + "\n\n" + section_body + "\n"


def ensure_doc_index(readme_path: Path) -> Tuple[bool, str]:
    if not readme_path.exists():
        return False, "skip: docs/README.md 不存在"

    content = readme_path.read_text(encoding="utf-8")
    marker = "- Harness 记录目录：`docs/harness/records/`"

    if marker in content:
        return False, "skip: 已包含 records 目录入口"

    lines = content.splitlines()
    insert_at = 1
    for idx, line in enumerate(lines):
        if line.startswith("- Harness 总则"):
            insert_at = idx + 1
            break

    lines.insert(insert_at, marker)

    changed = write_if_changed(readme_path, "\n".join(lines) + "\n")
    return changed, "insert: 增加 records 目录入口"


def is_agents_core_valid(content: str) -> bool:
    required = [
        "## 0. 读取顺序（Progressive Disclosure）",
        "## 1. 全局边界",
        "## 2. 统一工程基线",
        "## 3. 完成定义（仓库级）",
    ]
    return all(item in content for item in required)


def is_architecture_core_valid(content: str) -> bool:
    return "## L0：根目录（先看全局）" in content and "| 目录 | 作用 |" in content


def is_todo_core_valid(content: str) -> bool:
    return "- Intent：" in content and "- Constraints：" in content


def should_consider_root_alignment(task: str, intent: str, changed_files: List[str]) -> Tuple[bool, str]:
    text = f"{task} {intent}".lower()
    keywords = ["harness", "文档", "架构", "todo", "agents"]
    has_keyword = any(k in text for k in keywords)
    has_related_files = any(
        p in {"AGENTS.md", "ARCHITECTURE.md", "TODO.md", "docs/README.md"}
        or p.startswith("docs/")
        or p.startswith(".agents/skills/harness-doc-sync/")
        for p in changed_files
    )
    if has_keyword or has_related_files:
        return True, "hit: 任务文本或改动文件命中 Harness 文档域"
    return False, "skip: 本次任务与 Harness 根级入口无关"


def ensure_root_agents(agents_path: Path) -> Tuple[bool, str]:
    if not agents_path.exists():
        return False, "skip: AGENTS.md 不存在"

    content = agents_path.read_text(encoding="utf-8")
    if not is_agents_core_valid(content):
        return False, "skip: AGENTS.md 未满足核心结构"

    updated = remove_section(content, "## 4. 任务收尾提醒（Harness 文档同步）")
    updated = upsert_section(updated, ROOT_AGENTS_SECTION_TITLE, ROOT_AGENTS_SECTION_BODY)
    changed = write_if_changed(agents_path, updated)
    return changed, "upsert: 任务收尾提醒章节"


def ensure_architecture(architecture_path: Path) -> Tuple[bool, str]:
    if not architecture_path.exists():
        return False, "skip: ARCHITECTURE.md 不存在"

    content = architecture_path.read_text(encoding="utf-8")
    if not is_architecture_core_valid(content):
        return False, "skip: ARCHITECTURE.md 未满足核心导航结构"

    updated = re.sub(
        r"\n## L4：[\s\S]*?(?=\n##\s|\Z)",
        "\n",
        content,
        flags=re.MULTILINE,
    )

    if "L0-L3" not in updated:
        updated = updated.rstrip() + "\n\n" + ROOT_ARCHITECTURE_SINK_NOTE + "\n"

    changed = write_if_changed(architecture_path, updated)
    return changed, "normalize: 保持 L0-L3 导航并补充下沉说明"


def ensure_todo(todo_path: Path) -> Tuple[bool, str]:
    if not todo_path.exists():
        return False, "skip: TODO.md 不存在"

    content = todo_path.read_text(encoding="utf-8")
    if not is_todo_core_valid(content):
        return False, "skip: TODO.md 未满足核心任务结构"

    updated = upsert_section(content, ROOT_TODO_SECTION_TITLE, ROOT_TODO_SECTION_BODY)
    changed = write_if_changed(todo_path, updated)
    return changed, "upsert: Harness 文档对齐任务"


def write_record(
    records_dir: Path,
    task: str,
    intent: str,
    constraints: str,
    checks: str,
    dod: str,
    rollback: str,
    changed_files: List[str],
) -> Path:
    now = dt.datetime.now()
    timestamp = now.strftime(RECORD_TIMESTAMP_FORMAT)
    summary = sanitize_summary(task)
    filename = f"{timestamp}-{summary}.md"

    records_dir.mkdir(parents=True, exist_ok=True)
    record_path = records_dir / filename

    scopes = sorted({infer_scope(path) for path in changed_files})
    file_lines = "\n".join(f"- `{path}`" for path in changed_files) or "- `(no local file changes detected)`"

    content = (
        f"# {task}\n\n"
        f"- Time: {timestamp}\n"
        f"- Scope: {', '.join(scopes) if scopes else 'misc'}\n\n"
        f"## Intent\n{intent}\n\n"
        f"## Constraints\n{constraints}\n\n"
        f"## Checks\n{checks}\n\n"
        f"## DoD\n{dod}\n\n"
        f"## Rollback\n{rollback}\n\n"
        f"## Files\n{file_lines}\n"
    )
    record_path.write_text(content, encoding="utf-8")
    return record_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write one harness record file per AI coding task.")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--task", required=True, help="Change topic")
    parser.add_argument("--intent", help="Goal of this change")
    parser.add_argument("--constraints", default="不放宽仓库级 Harness 基线", help="Constraints")
    parser.add_argument("--checks", default="bun run typecheck && bun run test", help="Validation commands")
    parser.add_argument("--dod", default="文档入口可追踪，变更可复盘", help="Definition of done")
    parser.add_argument("--rollback", default="回退本次文档变更到上一版本", help="Rollback strategy")
    parser.add_argument("--records-dir", default="docs/harness/records", help="Harness records directory")
    parser.add_argument("--doc-readme", default="docs/README.md", help="Root docs index path")
    parser.add_argument("--root-agents", default="AGENTS.md", help="Root AGENTS path")
    parser.add_argument("--root-architecture", default="ARCHITECTURE.md", help="Root architecture path")
    parser.add_argument("--root-todo", default="TODO.md", help="Root TODO path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    records_dir = repo_root / args.records_dir
    readme_path = repo_root / args.doc_readme
    agents_path = repo_root / args.root_agents
    architecture_path = repo_root / args.root_architecture
    todo_path = repo_root / args.root_todo

    changed_files = collect_changed_files(repo_root)

    # 1) 优先写入记录文件，确保每次任务先沉淀事实。
    record_path = write_record(
        records_dir=records_dir,
        task=args.task,
        intent=args.intent or args.task,
        constraints=args.constraints,
        checks=args.checks,
        dod=args.dod,
        rollback=args.rollback,
        changed_files=changed_files,
    )

    changed_flags: List[Tuple[str, bool, str]] = []

    readme_changed, readme_reason = ensure_doc_index(readme_path)
    changed_flags.append((str(readme_path), readme_changed, readme_reason))

    should_align, align_reason = should_consider_root_alignment(args.task, args.intent or args.task, changed_files)
    if should_align:
        agents_changed, agents_reason = ensure_root_agents(agents_path)
        architecture_changed, architecture_reason = ensure_architecture(architecture_path)
        todo_changed, todo_reason = ensure_todo(todo_path)
        changed_flags.append((str(agents_path), agents_changed, agents_reason))
        changed_flags.append((str(architecture_path), architecture_changed, architecture_reason))
        changed_flags.append((str(todo_path), todo_changed, todo_reason))
    else:
        changed_flags.append((str(agents_path), False, align_reason))
        changed_flags.append((str(architecture_path), False, align_reason))
        changed_flags.append((str(todo_path), False, align_reason))

    print(f"Created: {record_path}")
    for path, changed, reason in changed_flags:
        state = "updated" if changed else "unchanged"
        print(f"{state}: {path} ({reason})")
    print(f"Tracked files: {len(changed_files)}")


if __name__ == "__main__":
    main()
