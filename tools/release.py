"""Bump the plugin's semver when any skill changed since the last release tag.

Run by CI on every push to main. It never pushes; the workflow commits and tags.

    python3 tools/release.py            # bump if needed, print the version to release
    python3 tools/release.py --dry-run  # say what would happen, change nothing

Rules:
- The last release is the newest tag named vX.Y.Z reachable from HEAD.
- No tag yet: release the version plugin.json already names, unchanged.
- Nothing the plugin ships (skills/, .mcp.json, .claude-plugin/) changed since the
  tag: nothing to release.
- A skill folder added or removed: minor bump. Any other change to what ships
  (a skill, the connectors, the manifest): patch bump.
- plugin.json already names a version above the tag (bumped by hand): keep it.
- Every changed skill's metadata.version is set to the new version, then the lock
  is rebuilt, so the lock and the tag always describe the same bytes.

Writes `version=<x.y.z>` and `release=<true|false>` to $GITHUB_OUTPUT when set.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
SKILLS_DIR = "skills"
SHIPPED = (SKILLS_DIR, ".mcp.json", ".claude-plugin")
TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
PLUGIN_VERSION = re.compile(r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")')
SKILL_VERSION = re.compile(r'^(  version:\s*")(\d+\.\d+\.\d+)(")', re.MULTILINE)

sys.path.insert(0, str(ROOT / "tools"))
import build_lock  # noqa: E402


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def parse(version: str) -> tuple[int, int, int]:
    major, minor, patch = (int(p) for p in version.split("."))
    return major, minor, patch


def last_tag() -> str | None:
    tags = [t for t in git("tag", "--merged", "HEAD", "--list", "v*").splitlines() if TAG.match(t)]
    if not tags:
        return None
    return max(tags, key=lambda t: parse(t[1:]))


def skill_names(ref: str | None) -> set[str]:
    if ref is None:
        return {p.name for p in (ROOT / SKILLS_DIR).iterdir() if (p / "SKILL.md").is_file()}
    listing = git("ls-tree", "--name-only", f"{ref}:{SKILLS_DIR}") if _has_path(ref) else ""
    return {name for name in listing.splitlines() if name}


def _has_path(ref: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{ref}:{SKILLS_DIR}"], cwd=ROOT, capture_output=True
    ).returncode == 0


def changed_files(tag: str) -> list[str]:
    return [line for line in git("diff", "--name-only", tag, "HEAD", "--", *SHIPPED).splitlines() if line]


def changed_skills(files: list[str]) -> set[str]:
    return {f.split("/")[1] for f in files if f.startswith(SKILLS_DIR + "/") and f.count("/") >= 2}


def write_output(**values: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            for key, value in values.items():
                fh.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest_text = PLUGIN.read_text(encoding="utf-8")
    current = json.loads(manifest_text)["version"]
    tag = last_tag()

    if tag is None:
        print(f"no release tag yet: release {current} as it is")
        write_output(version=current, release="true")
        return 0

    files = changed_files(tag)
    changed = changed_skills(files)
    if not files:
        print(f"nothing the plugin ships changed since {tag}: nothing to release")
        write_output(version=current, release="false")
        return 0

    before, after = skill_names(tag), skill_names(None)
    tagged = parse(tag[1:])
    if parse(current) > tagged:
        new = current
        reason = "plugin.json was bumped by hand"
    elif before != after:
        new = f"{tagged[0]}.{tagged[1] + 1}.0"
        reason = f"skills added or removed: +{sorted(after - before)} -{sorted(before - after)}"
    else:
        new = f"{tagged[0]}.{tagged[1]}.{tagged[2] + 1}"
        reason = "shipped files changed"
    present = sorted(changed & after)
    print(f"{tag} -> v{new} ({reason}); changed: {', '.join(files)}")

    if args.dry_run:
        return 0

    PLUGIN.write_text(PLUGIN_VERSION.sub(rf"\g<1>{new}\g<3>", manifest_text, count=1), encoding="utf-8")
    for name in present:
        skill = ROOT / SKILLS_DIR / name / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        updated, n = SKILL_VERSION.subn(rf"\g<1>{new}\g<3>", text, count=1)
        if n != 1:
            print(f"{name}: no metadata.version line to bump")
            return 1
        skill.write_text(updated, encoding="utf-8")

    lock, errors = build_lock.build()
    if errors:
        print("\n".join(errors))
        return 1
    build_lock.LOCK.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"bumped plugin.json and {len(present)} skill(s) to {new}; lock {lock['setDigest']}")
    write_output(version=new, release="true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
