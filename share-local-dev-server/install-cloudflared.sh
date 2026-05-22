#!/usr/bin/env bash
# install-cloudflared.sh — idempotent OS-aware installer for the Cloudflare
# Tunnel client. Called by the share-local-dev-server skill on first use.
#
# Exit codes:
#   0 — cloudflared is available on PATH after this script runs
#   1 — cloudflared is not available AND no auto-install path matched the
#       environment; the caller must install manually from
#       https://github.com/cloudflare/cloudflared/releases/latest

set -euo pipefail

# Already installed? Bail early — idempotent.
if command -v cloudflared >/dev/null 2>&1; then
  exit 0
fi

OS_KIND="$(uname -s)"
case "${OS_KIND}" in
  Darwin)
    # macOS — Homebrew is the canonical install path.
    if ! command -v brew >/dev/null 2>&1; then
      echo "install-cloudflared: macOS without Homebrew is unsupported." >&2
      echo "Install Homebrew first: https://brew.sh" >&2
      echo "Or download the binary directly:" >&2
      echo "  https://github.com/cloudflare/cloudflared/releases/latest" >&2
      exit 1
    fi
    echo "install-cloudflared: installing via Homebrew..."
    brew install cloudflared >/dev/null
    ;;

  Linux)
    # Linux — try apt first (Debian/Ubuntu), then yum/dnf (Fedora/RHEL).
    # We don't try apk (Alpine) because Alpine isn't on the supported list yet.
    if command -v apt-get >/dev/null 2>&1; then
      echo "install-cloudflared: installing via apt..."
      # The Cloudflare apt repo is the official path. We add it idempotently.
      if [ ! -f /etc/apt/sources.list.d/cloudflared.list ]; then
        sudo mkdir -p --mode=0755 /usr/share/keyrings
        curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
          | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
        echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] \
https://pkg.cloudflare.com/cloudflared $(. /etc/os-release && echo "$VERSION_CODENAME") main" \
          | sudo tee /etc/apt/sources.list.d/cloudflared.list >/dev/null
        sudo apt-get update -y >/dev/null
      fi
      sudo apt-get install -y cloudflared >/dev/null
    elif command -v dnf >/dev/null 2>&1; then
      echo "install-cloudflared: installing via dnf..."
      sudo dnf install -y \
        https://pkg.cloudflare.com/cloudflared-stable-linux-x86_64.rpm
    elif command -v yum >/dev/null 2>&1; then
      echo "install-cloudflared: installing via yum..."
      sudo yum install -y \
        https://pkg.cloudflare.com/cloudflared-stable-linux-x86_64.rpm
    else
      echo "install-cloudflared: no supported package manager (apt/dnf/yum) found." >&2
      echo "Download the binary directly and place it on PATH:" >&2
      echo "  https://github.com/cloudflare/cloudflared/releases/latest" >&2
      exit 1
    fi
    ;;

  *)
    echo "install-cloudflared: unsupported OS '${OS_KIND}'." >&2
    echo "Install cloudflared manually:" >&2
    echo "  https://github.com/cloudflare/cloudflared/releases/latest" >&2
    exit 1
    ;;
esac

# Sanity check
if ! command -v cloudflared >/dev/null 2>&1; then
  echo "install-cloudflared: install completed but cloudflared still not on PATH." >&2
  exit 1
fi

cloudflared --version
echo "install-cloudflared: ok"
