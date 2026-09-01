# Agent localization

Localization is display metadata only. Canonical Agent names, descriptions,
filenames, slugs, capabilities, tools, permissions, and prompt bodies remain
authoritative in the English Agent Markdown.

## Existing zh-CN Copilot localization

The existing Copilot workflow remains available and unchanged:

| File | Purpose |
|------|---------|
| `agent-names-zh.json` | English Agent name to Simplified Chinese metadata mapping |
| `localize-agents-zh.ps1` | Updates installed Copilot Agent copies under the selected target directories |

After installing Agents with `install.sh --tool copilot`, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/i18n/localize-agents-zh.ps1
```

By default the script processes `%USERPROFILE%\.github\agents\` and
`%USERPROFILE%\.copilot\agents\`. To select another installed-copy location:

```powershell
powershell -File scripts/i18n/localize-agents-zh.ps1 -TargetDirs @("C:\custom\path\agents")
```

This legacy workflow modifies installed Copilot copies only. It does not modify
the canonical Agent Markdown. Re-run it after an install that overwrites those
copies with canonical English metadata.

## New zh-TW metadata localization

`agent-metadata-zh-TW.json` is the Taiwan Traditional Chinese display layer for
the canonical English catalog. Schema v1 keys `agents` by canonical source
filename stem. Each row contains:

- the canonical `sourceName`;
- a `sourceDescriptionSha256` freshness guard;
- localized display-only `name` and `description` fields.

The description guard is lowercase SHA-256 of the UTF-8 canonical description
after parsing its YAML scalar. Folded continuation lines are joined with one
ASCII space, and surrounding YAML quotes are excluded.

`source-association.json` records the controlled source repository, approved
baseline, durable default ref, resource path, and authoritative resource hash.
The App mirror must remain byte-identical to both source files.

## Codex zh-TW usage

Canonical English conversion remains the default:

```bash
./scripts/convert.sh --tool codex
./scripts/convert.sh --tool codex --locale en
```

To render bilingual human-readable Codex metadata:

```bash
./scripts/convert.sh --tool codex --locale zh-TW
```

The zh-TW render changes only the TOML `name` and `description` display values.
The canonical English name is retained, `developer_instructions` remains the
canonical body, and the generated filename is still derived before localization.

## Validation and governance

Run:

```bash
python3 scripts/validate-localization.py
./scripts/test-convert-frontmatter.sh
```

The validator is standard-library only and never mutates canonical sources. It
checks schema and locale, missing/stale/orphan mappings, empty or malformed
fields, duplicate JSON keys and localized names, high-confidence Simplified
Chinese characters, canonical description guards, source association, and the
authoritative resource SHA-256.

For cross-repository parity, CI first looks for a counterpart branch with the
same PR/head branch name. If none exists, it falls back to the durable `main`
ref recorded by `sourceDefaultRef`. This allows feature development without a
permanent feature-branch dependency. After the source localization changes are
committed, update the association metadata when governance requires a new
approved baseline or content hash; never substitute a mutable display name for
the resource SHA-256.
