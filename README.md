# kutana-skills

Externally-shippable agent skills for [Kutana](https://kutana.ai). Author once, ship everywhere — Claude Code plugins, CoWork connectors, Codex, OpenClaw, and any other agentic platform with a skill primitive.

## What's in here

Each subdirectory is a self-contained skill following the [Anthropic Agent Skill](https://code.claude.com/docs/en/skills) spec — `SKILL.md` with YAML frontmatter, plus optional supporting scripts and example configs.

| Skill | Triggers on | What it does |
|---|---|---|
| [`kutana-meeting`](./kutana-meeting/) | "meeting", "kutana", "standup", "call", "hand raise", "speaker", "transcript", "action items", "join meeting" | Connects an agent to a Kutana meeting via MCP — list/join meetings, request speaker turns, send chat, fetch transcripts, create tasks. |
| [`share-local-dev-server`](./share-local-dev-server/) | "share screen", "demo", "dev server", "show this in the meeting", "live preview", "walk through this" | Provisions a per-meeting Cloudflare Tunnel for the agent's local dev server and embeds a live Browserbase view in the meeting's ArtifactPanel — the unified-tunnel architecture (v2). |

## Why a separate repo

These skills are consumed by multiple platforms outside the Kutana monorepo (Claude Code plugin marketplace, CoWork connector catalog, etc.). Living in their own repo means:

- One canonical source — no drift between consumers.
- Independent release cadence — skills version separately from Kutana's backend.
- Plugin-portable from day one — each skill is structured as a drop-in for any agent platform.

## How to use a skill

Each `SKILL.md` is loadable directly by any platform that follows the Anthropic Agent Skill spec. For Claude Code specifically, this repo is also packaged as the `kutana` plugin (see `.claude-plugin/plugin.json`) — install it via:

```bash
# Coming soon — Claude Code plugin marketplace
```

For now, point your agent platform at the skill source by filesystem path or git submodule. See each skill's `SKILL.md` for connection setup.

## Authoring a new skill

1. Create a new directory: `mkdir <skill-name>`
2. Drop in `SKILL.md` with YAML frontmatter (`name`, `description`, `allowed-tools`).
3. Add any supporting scripts (`*.sh`, `*.py`) referenced by the SKILL.md body.
4. Keep the skill self-contained — no imports from Kutana's backend; only call documented MCP tools.
5. PR. CI lints the frontmatter and shell scripts.

## Related projects

- [`kutana-ai-web`](https://github.com/kutana-ai/kutana-ai-web) — the Kutana backend + frontend monorepo. Includes this repo as a git submodule at `skills/`.
- [Kutana docs](https://kutana.ai) — product docs and onboarding.

## License

MIT — see [`LICENSE`](./LICENSE).
