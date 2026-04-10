#!/usr/bin/env sh
set -eu

REPO="zhiqli1993/knowledge-base"
INSTALL_DIR="${KB_INSTALL_DIR:-$HOME/.local/bin}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_cmd curl
need_cmd tar

OS_NAME="$(uname -s)"
case "$OS_NAME" in
  Darwin) PLATFORM="darwin" ;;
  Linux) PLATFORM="linux" ;;
  *)
    echo "Unsupported operating system: $OS_NAME" >&2
    exit 1
    ;;
esac

ARCH_NAME="$(uname -m)"
if [ "$PLATFORM" = "darwin" ]; then
  case "$ARCH_NAME" in
    x86_64|amd64) ARCH="x64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *)
      echo "Unsupported macOS architecture: $ARCH_NAME" >&2
      exit 1
      ;;
  esac
else
  case "$ARCH_NAME" in
    x86_64|amd64) ARCH="x64" ;;
    arm64|aarch64)
      echo "Linux ARM64 binaries are not published yet. Please use the Python package install for now." >&2
      exit 1
      ;;
    *)
      echo "Unsupported Linux architecture: $ARCH_NAME" >&2
      exit 1
      ;;
  esac
fi

ASSET="kb-${PLATFORM}-${ARCH}.tar.gz"
URL="https://github.com/${REPO}/releases/latest/download/${ASSET}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

mkdir -p "$INSTALL_DIR"
curl -fsSL "$URL" -o "$TMP_DIR/$ASSET"
tar -xzf "$TMP_DIR/$ASSET" -C "$TMP_DIR"

BUNDLE_DIR="$TMP_DIR/kb-${PLATFORM}-${ARCH}"
for binary in kb kb-http kb-mcp; do
  cp "$BUNDLE_DIR/$binary" "$INSTALL_DIR/$binary"
  chmod 0755 "$INSTALL_DIR/$binary"
done

echo "Installed kb, kb-http, and kb-mcp to $INSTALL_DIR"
case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *) echo "Add $INSTALL_DIR to your PATH to use the commands directly." ;;
esac
echo "Prerequisites: install Git and Ollama, then run 'ollama pull nomic-embed-text'."
