#!/usr/bin/env bash
# Regression coverage for YAML frontmatter emitted by convert.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agency-convert-frontmatter.XXXXXX")"
trap 'rm -rf "$OUTPUT_DIR"' EXIT

for tool in gemini-cli opencode qwen; do
  "$SCRIPT_DIR/convert.sh" --tool "$tool" --out "$OUTPUT_DIR" >/dev/null
done

CODEX_DEFAULT="$OUTPUT_DIR/codex-default"
CODEX_EN="$OUTPUT_DIR/codex-en"
CODEX_ZH="$OUTPUT_DIR/codex-zh"
"$SCRIPT_DIR/convert.sh" --tool codex --out "$CODEX_DEFAULT" >/dev/null
"$SCRIPT_DIR/convert.sh" --tool codex --locale en --out "$CODEX_EN" >/dev/null
"$SCRIPT_DIR/convert.sh" --tool codex --locale zh-TW --out "$CODEX_ZH" >/dev/null

# Explicit English remains byte-identical to the historical default.
diff -ru "$CODEX_DEFAULT/codex" "$CODEX_EN/codex"
# Display localization never changes generated filenames.
diff <(find "$CODEX_EN/codex/agents" -type f -printf '%f\n' | sort) <(find "$CODEX_ZH/codex/agents" -type f -printf '%f\n' | sort)

python3 - "$REPO_ROOT" "$CODEX_EN" "$CODEX_ZH" <<'PY'
import sys
import tomllib
from pathlib import Path

repo, en_root, zh_root = map(Path, sys.argv[1:])
en = tomllib.loads((en_root / "codex/agents/ai-engineer.toml").read_text(encoding="utf-8"))
zh = tomllib.loads((zh_root / "codex/agents/ai-engineer.toml").read_text(encoding="utf-8"))
assert en["name"] == "AI Engineer"
assert zh["name"] == "AI Engineer｜AI 工程師"
assert zh["description"].startswith(en["description"] + "\n\n中文：\n")

# Localization is a display-only transform: its prompt must remain byte-for-byte
# identical to the converter's canonical English output. Do not reconstruct the
# body with a simplified frontmatter split here; canonical prompts may contain
# their own `---` separators and convert.sh's historical extraction is out of
# scope for localization.
assert zh["developer_instructions"] == en["developer_instructions"]
PY

if "$SCRIPT_DIR/convert.sh" --tool codex --locale zh-CN --out "$OUTPUT_DIR/invalid" >/dev/null 2>&1; then
  echo "Expected unsupported locale to fail" >&2
  exit 1
fi

assert_quoted() {
  local file="$1" field="$2" line prefix
  line="$(awk -v key="$field" '$0 ~ "^" key ":" { print; exit }' "$file")"
  prefix="$field: '"
  [[ "$line" == "$prefix"*"'" ]] || {
    printf 'Expected %s in %s to be a single-quoted YAML scalar, got: %s\n' \
      "$field" "$file" "$line" >&2
    return 1
  }
}

assert_quoted \
  "$OUTPUT_DIR/gemini-cli/agents/developer-tooling-engineer.md" \
  description
assert_quoted \
  "$OUTPUT_DIR/opencode/agents/developer-tooling-engineer.md" \
  name
assert_quoted \
  "$OUTPUT_DIR/opencode/agents/developer-tooling-engineer.md" \
  description
assert_quoted \
  "$OUTPUT_DIR/qwen/agents/programmatic-display-buyer.md" \
  tools

echo "PASS: YAML quoting and Codex en/zh-TW localization invariants"
