"""Lint the Kutana skill folders and write (or check) skills.lock.json.

The lock is the one record of what Kutana publishes: every file of every skill
with the same {uri, digest, size} triple the MCP Skills extension (SEP-2640)
puts in a skills/list manifest. The plugin ships it, CI refuses a change that
does not regenerate it, and a connecting host can compare a server's listing
against it.

Usage:
    python3 tools/build_lock.py            # lint, then write skills.lock.json
    python3 tools/build_lock.py --check    # lint, then fail if the lock is stale (CI)
    python3 tools/build_lock.py --lint     # lint only

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
LOCK = ROOT / "skills.lock.json"
PUBLISHER = "kutana-ai"

# Markdown outside the skills that is also public copy and gets the same lint.
EXTRA_MARKDOWN = ("README.md",)

# Agent-visible copy rules. Mirrors the mcp-server agent-visible naming guard
# plus the product words skills must not use. "meeting prep" needs a space or
# hyphen, so tool ids such as kutana_admin_set_meeting_prep pass while the
# phrase does not. Code spans and code blocks are stripped before the check.
BANNED = re.compile(
    r"(?<![a-z])(previews?|previewing|previewed|stages?|staged|staging|sandbox(?:es|ed|ing)?"
    r"|demos?|jarvis|feeds?|free|meeting[ -]prep)(?![a-z])",
    re.IGNORECASE,
)
# Skills never name a model: the person's client picks it.
MODEL_NAMES = re.compile(
    r"(?<![a-z])(opus|sonnet|haiku|gpt-?\d[\w.-]*|gpt|gemini|claude-[0-9a-z.-]*\d[\w.-]*)(?![a-z])",
    re.IGNORECASE,
)
EM_DASH = "—"
CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
CODE_SPAN = re.compile(r"`[^`\n]*`")
ITALIC_STAR = re.compile(r"(?<![*\w])\*(?![\s*])[^*\n]+?(?<![\s*])\*(?![*\w])")
ITALIC_UNDER = re.compile(r"(?<![\w_])_(?![\s_])[^_\n]+?(?<![\s_])_(?![\w_])")
NAME_RULE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
TOOL_NAME = re.compile(r"(?<![\w])kutana_[a-z0-9_]*[a-z0-9](?![\w])")
KNOWN_TOOLS = ROOT / "tools" / "known_tools.txt"
# Hostnames that must never appear in this public repo.
PRIVATE_HOST = re.compile(r"\.local\b|\.internal\b|\.ts\.net\b|\.lan\b|\b10\.\d+\.\d+\.\d+\b|\b192\.168\.")


def frontmatter(text: str) -> dict[str, str]:
    """Top-level and metadata.* scalar keys of a SKILL.md frontmatter block."""
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with a --- frontmatter block")
    block = text[4 : text.index("\n---", 4)]
    out: dict[str, str] = {}
    parent = ""
    for line in block.splitlines():
        if not line.strip():
            continue
        key, _, value = line.strip().partition(":")
        value = value.strip().strip('"')
        if line.startswith("  ") and parent:
            out[f"{parent}.{key}"] = value
        else:
            parent = key if not value else ""
            out[key] = value
    return out


def lint_markdown(rel: str, text: str) -> list[str]:
    errors: list[str] = []
    for n, line in enumerate(text.splitlines(), 1):
        if PRIVATE_HOST.search(line):
            errors.append(f"{rel}:{n}: private hostname or address")
    prose = CODE_SPAN.sub("", CODE_BLOCK.sub("", text))
    for n, line in enumerate(prose.splitlines(), 1):
        for m in BANNED.finditer(line):
            errors.append(f"{rel}:{n}: banned word '{m.group(0)}'")
        for m in MODEL_NAMES.finditer(line):
            errors.append(f"{rel}:{n}: model name '{m.group(0)}'")
        if EM_DASH in line:
            errors.append(f"{rel}:{n}: em dash")
        if ITALIC_STAR.search(line) or ITALIC_UNDER.search(line):
            errors.append(f"{rel}:{n}: italics")
    return errors


def lint_other(rel: str, text: str) -> list[str]:
    """Non-markdown files: only the rules that apply to any text."""
    errors: list[str] = []
    for n, line in enumerate(text.splitlines(), 1):
        if PRIVATE_HOST.search(line):
            errors.append(f"{rel}:{n}: private hostname or address")
        if EM_DASH in line:
            errors.append(f"{rel}:{n}: em dash")
    return errors


def known_tools() -> tuple[set[str], set[str]]:
    """(live, pending) tool names from tools/known_tools.txt."""
    live: set[str] = set()
    pending: set[str] = set()
    for line in KNOWN_TOOLS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, flag = line.partition(" ")
        (pending if flag.strip() == "pending" else live).add(name)
    return live, pending


def lint_tools(rel: str, text: str, live: set[str], pending: set[str]) -> list[str]:
    errors: list[str] = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in TOOL_NAME.finditer(line):
            if m.group(0) not in live and m.group(0) not in pending:
                errors.append(f"{rel}:{n}: unknown tool '{m.group(0)}' (not in tools/known_tools.txt)")
    names = set(TOOL_NAME.findall(text))
    if names & pending and not names & live:
        errors.append(f"{rel}: names only pending tools; add a fallback to live ones")
    return errors


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def build() -> tuple[dict, list[str]]:
    errors: list[str] = []
    skills = []
    live, pending = known_tools()
    for folder in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        main = folder / "SKILL.md"
        if not main.is_file():
            errors.append(f"{folder.name}: no SKILL.md")
            continue
        fm = frontmatter(main.read_text(encoding="utf-8"))
        name = fm.get("name", "")
        if name != folder.name or not NAME_RULE.match(name):
            errors.append(f"{folder.name}: name '{name}' must be kebab-case and equal the folder")
        if not fm.get("description"):
            errors.append(f"{folder.name}: description is required")
        if "allowed-tools" in fm:
            errors.append(f"{folder.name}: allowed-tools is not used by Kutana skills")
        if fm.get("metadata.publisher") != PUBLISHER:
            errors.append(f"{folder.name}: metadata.publisher must be {PUBLISHER}")
        if not SEMVER.match(fm.get("metadata.version", "")):
            errors.append(f"{folder.name}: metadata.version must be semver (x.y.z)")
        files = []
        for path in sorted(p for p in folder.rglob("*") if p.is_file() or p.is_symlink()):
            if path.is_symlink():
                errors.append(f"{path.relative_to(SKILLS)}: symlinks are not allowed")
                continue
            if path.name == ".DS_Store" or "__pycache__" in path.parts:
                continue
            data = path.read_bytes()
            rel = path.relative_to(folder).as_posix()
            text = data.decode("utf-8")
            if path.suffix == ".md":
                errors += lint_markdown(f"skills/{folder.name}/{rel}", text)
                errors += lint_tools(f"skills/{folder.name}/{rel}", text, live, pending)
            else:
                errors += lint_other(f"skills/{folder.name}/{rel}", text)
            files.append(
                {"uri": f"skill://{folder.name}/{rel}", "digest": sha256(data), "size": len(data)}
            )
        if len(files) > 512 or sum(f["size"] for f in files) > 16 * 1024 * 1024:
            errors.append(f"{folder.name}: over the SEP-2640 limits (512 files, 16 MiB)")
        skills.append(
            {
                "name": name,
                "version": fm.get("metadata.version", ""),
                "uri": f"skill://{folder.name}/SKILL.md",
                "resources": files,
            }
        )
    for extra in EXTRA_MARKDOWN:
        path = ROOT / extra
        if path.is_file():
            errors += lint_markdown(extra, path.read_text(encoding="utf-8"))
    for extra in (".mcp.json", ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        path = ROOT / extra
        if path.is_file():
            errors += lint_other(extra, path.read_text(encoding="utf-8"))
    body = {"publisher": PUBLISHER, "skills": skills}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    lock = {"lockVersion": 1, "setDigest": sha256(canonical), **body}
    return lock, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fail if the lock is stale")
    mode.add_argument("--lint", action="store_true", help="lint only, never write")
    args = parser.parse_args()
    lock, errors = build()
    if errors:
        print("\n".join(errors))
        print(f"{len(errors)} problem(s)")
        return 1
    if args.lint:
        print(f"lint clean: {len(lock['skills'])} skills")
        return 0
    text = json.dumps(lock, indent=2) + "\n"
    if args.check:
        if not LOCK.exists() or LOCK.read_text(encoding="utf-8") != text:
            print("skills.lock.json is stale: run python3 tools/build_lock.py and commit it")
            return 1
        print(f"lint clean, lock current: {len(lock['skills'])} skills, {lock['setDigest']}")
        return 0
    LOCK.write_text(text, encoding="utf-8")
    print(f"wrote {LOCK.relative_to(ROOT)}: {len(lock['skills'])} skills, {lock['setDigest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
