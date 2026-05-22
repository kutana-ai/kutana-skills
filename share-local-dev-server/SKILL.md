---
name: share-local-dev-server
description: >
  Provision a per-meeting Cloudflare Tunnel for the agent's local dev server
  and embed a live Browserbase view in the meeting's ArtifactPanel so every
  participant sees the running app like a screen-share. TRIGGER on: share
  screen, demo, show this, dev server, vite, npm dev, "let everyone see what
  I built", live preview, walk through this.
allowed-tools:
  - Bash
  - kutana_tunnel_create
  - kutana_browse
  - kutana_artifact
---

# Share Local Dev Server

Use this skill when a meeting participant asks you to **show a running app live** — a Vite dev server, a Next.js dev build, a Streamlit dashboard, anything bound to `localhost:<port>` in the environment you control. The skill turns that local port into a public URL via a per-meeting [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/), hands the URL to Browserbase to render in a streamable cloud browser, and embeds that browser view in the meeting's ArtifactPanel.

## Prerequisites

- You're in a meeting (Kutana MCP server is connected; `kutana_*` tools are available).
- The dev server is running OR you can start it on a known local port (`5173`, `3000`, `8501`, etc.). If it isn't running yet, start it first — see step 2.

## Recipe

### 1. Verify cloudflared is installed

```bash
if ! command -v cloudflared >/dev/null 2>&1; then
  bash install-cloudflared.sh
fi
cloudflared --version
```

Kutana-managed agents have `cloudflared` pre-installed via `packages.apt`. Other environments (Claude Code on a developer's machine, CoWork agents, etc.) auto-install via `install-cloudflared.sh` — see the script in this skill directory.

### 2. Start the dev server (if not already running)

Use whatever the project's normal dev command is. Examples:

```bash
# Vite frontend
pnpm dev &
DEV_PID=$!
PORT=5173

# Next.js
npm run dev &
DEV_PID=$!
PORT=3000

# Streamlit
streamlit run app.py --server.port 8501 &
DEV_PID=$!
PORT=8501
```

Wait until the server is listening:

```bash
until curl -fsS "http://localhost:${PORT}" >/dev/null 2>&1; do sleep 1; done
echo "Dev server up on http://localhost:${PORT}"
```

> **Tip:** the dev command stays in the background for the duration of the meeting. Don't `&& wait` — that would block the rest of the recipe.

### 3. Provision a per-meeting tunnel

```
kutana_tunnel_create(local_port=${PORT})
```

Returns:

```json
{
  "public_url": "https://coding-partner-meeting-<meeting_id>.kutana.ai",
  "run_token": "<opaque base64 — never paste, log, or echo this in chat>",
  "tunnel_id": "<uuid>",
  "expires_at": "2026-05-22T..."
}
```

The token is **single-use, non-transferable, scoped to this meeting**. Do not log it, send it to chat, or store it outside the agent environment. It is cleaned up automatically when the meeting ends (the `meeting.ended` event triggers a tunnel-delete via the registry pattern).

### 4. Bring the tunnel client online

```bash
cloudflared tunnel run --token "<run_token from step 3>" >/tmp/cloudflared.log 2>&1 &
TUNNEL_PID=$!
```

Wait for the tunnel to be live:

```bash
until curl -fsS "${PUBLIC_URL}" -o /dev/null; do sleep 1; done
echo "Tunnel live: ${PUBLIC_URL}"
```

### 5. Open the URL in Browserbase and embed the live view in the meeting

```
kutana_browse(url="${PUBLIC_URL}", slug="dev-preview")
```

`kutana_browse` does two things in one call: it opens a Browserbase session at the URL **and** internally publishes the Live View as a meeting artifact (slug-keyed). Returns `{session_id, live_view_url, terminates_at, artifact_id}`. Every meeting participant now sees the live app in the right-rail ArtifactPanel.

If you want a different slug or to keep the artifact pinned across re-emits, you can also call `kutana_artifact(url=live_view_url, slug="...", pinned=true)` explicitly — but for the standard demo flow, the single `kutana_browse` call is enough.

## Common follow-ups

- **Walk participants through a feature.** The Browserbase session is drivable — interact with the app and participants see the changes stream live in the ArtifactPanel.
- **Update the embed.** Re-emit `kutana_browse(url=NEW_URL, slug="dev-preview")` with the same slug to replace the artifact in place. Use `kutana_artifact(slug="dev-preview", html="<empty>")` to clear it.
- **Stop sharing.** `kutana_browse_terminate(session_id=...)` ends the Browserbase session. The tunnel itself is cleaned up automatically when the meeting ends.

## Write-op safety

If you need to commit + push code (e.g., applying a fix you and the participants just discussed), do it through `kutana_bash` rather than the built-in bash tool. `kutana_bash` surfaces a PermissionBubble for git push, npm publish, sudo, and other destructive operations — participants click Allow/Deny inline before the action runs. The built-in bash tool bypasses this safety layer.

```
kutana_bash(command="git push origin feature/walkthrough-fix")
# → PermissionBubble appears in the meeting
# → on Allow: push proceeds and you continue
# → on Deny: returns a blocked-envelope so you can explain and choose differently
```

## Troubleshooting

- **`cloudflared not found` after the install step.** The install script supports macOS (Homebrew) and Debian/Ubuntu (apt). On Alpine or stripped containers, install the binary directly from `https://github.com/cloudflare/cloudflared/releases/latest` and place it on `$PATH`.
- **Tunnel comes up but `curl ${PUBLIC_URL}` returns 502/503.** The dev server isn't bound to `localhost:${PORT}` (some frameworks bind to `0.0.0.0` only, or to a different interface). Re-run with `--host 0.0.0.0` or whatever the framework's "bind to all interfaces" flag is.
- **Browserbase says "rate limit reached" or similar.** A previous session may not have closed. Wait 30s and retry; otherwise the meeting-end cleanup will sweep stale sessions.

## Related

- The architecture doc: `internal-docs/operations/coding-agent-demo-architecture.html` (v2) in the kutana-ai-web repo.
- The MCP tools this skill orchestrates (`kutana_tunnel_create`, `kutana_browse`, `kutana_artifact`) live in `services/mcp-server/` in the kutana-ai-web repo.
- The `kutana-meeting` skill (sibling in this repo) handles the prerequisite of "agent joins a meeting" — connect MCP first, then this skill takes over for the share-screen flow.
