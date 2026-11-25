#!/usr/bin/env python3
"""Safely initialize or check durable project-continuity files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


START = "<!-- maintain-project-memory:start -->"
END = "<!-- maintain-project-memory:end -->"


def choose_memory(root: Path, requested: str | None) -> Path:
    if requested:
        path = (root / requested).resolve()
        if root != path and root not in path.parents:
            raise ValueError("memory file must stay inside the project root")
        return path

    preferred = [root / "PROJECT_MEMORY.md"]
    preferred.extend(sorted(root.glob("*_PROJECT_MEMORY.md")))
    preferred.append(root / "MEMORY.md")
    for path in preferred:
        if path.is_file():
            return path
    return root / "PROJECT_MEMORY.md"


def managed_block(memory_name: str) -> str:
    return f"""{START}
## Project continuity

- At the start of a task, read `{memory_name}` before planning or changing files.
- Treat its status as a handoff snapshot: verify important files, Git state, tests, artifacts, and external jobs before relying on them.
- Update `{memory_name}` after material milestones, decisions, failures, or background-job transitions, and before a long-session handoff.
- Keep verified results separate from pending plans. Preserve frozen protocols, data splits, and explicit invariants.
- Never write passwords, tokens, private keys, cookies, or credential-bearing URLs into project memory.
{END}"""


def memory_template(project_name: str) -> str:
    stamp = datetime.now().astimezone().isoformat(timespec="minutes")
    return f"""# {project_name} Project Memory

## Last verified

- {stamp}

## Objective

- PENDING: Describe the stable project goal and current phase.

## Current state

- PENDING: Record only facts verified in this workspace.

## Verified results and evidence

- PENDING: Add tests, metrics, commits, artifacts, and supporting paths.

## Decisions and invariants

- PENDING: Add frozen protocols, interfaces, data splits, and constraints.

## Important files and paths

- PENDING: Add the canonical plans, reports, code, data, and output paths.

## External systems and background jobs

- PENDING: Add last-checked state and safe inspection commands. Do not add credentials.

## Immediate continuation

1. PENDING: State the exact first action for the next session.

## Blockers and unknowns

- None recorded.

## Update history

- {stamp}: Continuity files initialized.
"""


def update_agents(path: Path, block: str) -> str:
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if START in text and END in text:
            before, rest = text.split(START, 1)
            _, after = rest.split(END, 1)
            new_text = before.rstrip() + "\n\n" + block + after
            action = "updated-managed-block"
        else:
            new_text = text.rstrip() + "\n\n" + block + "\n"
            action = "appended-managed-block"
    else:
        new_text = "# Project Instructions\n\n" + block + "\n"
        action = "created"
    path.write_text(new_text, encoding="utf-8")
    return action


def check(root: Path, memory: Path, agents: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not memory.is_file():
        issues.append(f"missing memory file: {memory}")
    if not agents.is_file():
        issues.append(f"missing AGENTS.md: {agents}")
    else:
        text = agents.read_text(encoding="utf-8")
        if START not in text or END not in text:
            issues.append("AGENTS.md is missing the managed continuity block")
        rel = memory.relative_to(root).as_posix()
        if rel not in text:
            issues.append(f"AGENTS.md does not reference {rel}")
    return not issues, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--memory-file", help="Path relative to project root")
    parser.add_argument("--project-name")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"project root does not exist: {root}")
    memory = choose_memory(root, args.memory_file)
    agents = root / "AGENTS.md"

    if args.check:
        ok, issues = check(root, memory, agents)
        print(json.dumps({"ok": ok, "issues": issues}, ensure_ascii=False, indent=2))
        return 0 if ok else 1

    memory.parent.mkdir(parents=True, exist_ok=True)
    memory_action = "preserved"
    if not memory.exists():
        name = args.project_name or root.name
        memory.write_text(memory_template(name), encoding="utf-8")
        memory_action = "created"

    relative_memory = memory.relative_to(root).as_posix()
    agents_action = update_agents(agents, managed_block(relative_memory))
    ok, issues = check(root, memory, agents)
    print(json.dumps({
        "ok": ok,
        "project_root": str(root),
        "memory_file": str(memory),
        "memory_action": memory_action,
        "agents_action": agents_action,
        "issues": issues,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
