# Kutana Skills

The **`kutana`** Claude plugin: both [Kutana AI](https://kutana.ai) connectors plus the
skills that teach an agent to use them. Plain `SKILL.md` folders, so any platform that
reads the Agent Skills format can load them too.

## Install in Claude Code

```text
/plugin marketplace add kutana-ai/kutana-skills
/plugin install kutana@kutana-ai
```

Claude Code asks for two values at install and keeps them in your system's credential
store. Nothing is written to this repo or to your project.

| Value | Where to get it | Used by |
| --- | --- | --- |
| **Agent key** (`cvn_...`) | Kutana, **Agents**, your custom agent, **API Keys** | the `kutana` connector: joining meetings, sharing your screen |
| **Access token** (`kpat_...`) | Kutana, **Settings**, **Developer**, **Access Tokens** | the `kutana-admin` connector: meeting context, Assignments, Messages |

Leave a value blank if you only need the other connector. Try it for one session without
installing: `claude --plugin-dir /path/to/kutana-skills`.

## Skills

Shown in Claude Code as `kutana:<name>`.

| Skill | Connector | What it teaches |
| --- | --- | --- |
| [`run-a-meeting`](skills/run-a-meeting/SKILL.md) | `kutana` | Join, listen, take turns, record decisions and action items, show work, facilitate, leave |
| [`share-your-screen`](skills/share-your-screen/SKILL.md) | `kutana` | Pick or build an app image, share it as a live tile, check your own page, change it live, stop |
| [`catch-up-on-a-meeting`](skills/catch-up-on-a-meeting/SKILL.md) | `kutana-admin` | Brief on a meeting, find meetings, close an action item with a link, search an agent's memory |
| [`file-an-assignment`](skills/file-an-assignment/SKILL.md) | `kutana-admin` | Give a managed agent work before a meeting, after one or on a schedule; run it and read the result |
| [`answer-your-agents`](skills/answer-your-agents/SKILL.md) | `kutana-admin` | Read Messages threads, answer questions, approve or decline changes, steer a run |

These skills are for agents and clients you connect to Kutana yourself. Kutana does not
attach them to the managed agents that run inside a meeting.

## Layout

```text
.claude-plugin/plugin.json        plugin manifest (name, version, the two install values)
.claude-plugin/marketplace.json   one-plugin marketplace, so /plugin install works
.mcp.json                         the kutana and kutana-admin connectors
skills/<name>/SKILL.md            one folder per skill, plus references/ and scripts/
skills.lock.json                  SHA-256 and size of every skill file (generated)
tools/build_lock.py               copy lint + lock writer and checker
tools/release.py                  semver bump on any skill change (run by CI)
tools/known_tools.txt             every tool name the connectors expose; skills may name only these
```

## Trust and Versioning

- **One source.** This repo is the only home of these skills. Copies elsewhere are
  generated from it.
- **Content lock.** `skills.lock.json` records the SHA-256 digest and size of every file
  in every skill, in the same shape an MCP `skills/list` manifest uses. CI fails a change
  that does not regenerate it.
- **Pinned versions.** The plugin `version` is semver. On every merge to `main` that
  changes a skill, CI bumps the version (minor when a skill is added or removed, patch
  otherwise), updates each changed skill's `metadata.version`, rebuilds the lock, commits
  and tags `vX.Y.Z`. You stay on a version until you update.
- **No hidden permissions.** No skill sets `allowed-tools`. Scripts are standard-library
  Python with no network access and no file writes; anything that touches Kutana data goes
  through a connector tool, where scopes and the audit log apply.

## Authoring a Skill

1. Create `skills/<kebab-name>/SKILL.md` with frontmatter: `name` (equal to the folder),
   `description`, and `metadata.publisher: kutana-ai` plus `metadata.version`.
2. Name only tools the Kutana connectors expose today (`tools/known_tools.txt`). A tool
   marked `pending` there may be named only next to a fallback to live tools.
3. Copy rules (the lint enforces them, outside code spans):
   - Bullets with bold key nouns; Title Case for names on screen (Messages, Brief, Assignments).
   - No em dashes and no italics.
   - None of the banned words in `tools/build_lock.py`, including the retired names for
     Integrations and Assignments.
   - No model names.
4. Run `python3 tools/build_lock.py` and commit the updated `skills.lock.json`.
5. Open a pull request. CI runs the lint, the lock check and `claude plugin validate`.
   Do not bump versions by hand; CI does it on merge.

## License

MIT, see [`LICENSE`](./LICENSE).
