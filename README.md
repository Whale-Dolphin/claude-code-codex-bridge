# claude-code-codex-bridge

A Codex skill for installing, configuring, verifying, and troubleshooting a local [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) bridge from Codex OAuth to Claude Code.

## What it configures

- A localhost-only CLIProxyAPI service backed by Codex OAuth
- Separate `gpt-6-astra-fast` and `gpt-5.6-sol-fast` client aliases, each requesting `xhigh` reasoning and Priority processing
- Claude Code `/model` mappings with Fable as the default Astra Fast route and Opus as the Sol Fast route
- A 1M Claude Code managed context profile for both Fast routes, activated with `[1m]` model suffixes and scoped only to `claudex`
- A hardened user-level systemd service
- End-to-end model-list, normal-route, Fast-route, and shell validation

## Default Claude Code mappings

| Claude Code label | Model | Reasoning / processing |
| --- | --- | --- |
| Fable (default) | `gpt-6-astra-fast[1m]` | `xhigh` / requested Priority |
| Opus | `gpt-5.6-sol-fast[1m]` | `xhigh` / requested Priority |
| Sonnet | `gpt-5.6-terra` | Existing provider behavior |
| Haiku | `gpt-5.6-luna` | Existing provider behavior |
| Subagent | `gpt-6-astra-fast[1m]` | `xhigh` / requested Priority |

Each Fast entry is a client-visible alias for its canonical upstream model (`gpt-6-astra` or `gpt-5.6-sol`). Keep `fork: true` so the canonical routes remain available. The bridge overrides `reasoning.effort: xhigh` and `service_tier: priority` only for the two Fast aliases. `claudex` launches with `--model fable --effort xhigh`; use `claudex --model opus` or `/model` to select Sol Fast.

The `[1m]` suffix belongs to the Claude Code-facing names; Terra and Luna remain unsuffixed, and CLIProxyAPI's aliases and canonical IDs remain unsuffixed. The skill reports Priority processing as confirmed only when upstream response metadata confirms it. A successful Fast alias response alone does not establish a Priority grant.

## 1M context management

The skill combines Claude Code-facing `[1m]` suffixes on Astra Fast and Sol Fast with this client-side context setting inside the `claudex` alias:

```zsh
CLAUDE_CODE_MAX_CONTEXT_TOKENS="1000000"
```

The suffix activates Claude Code's 1M model profile, while the environment variable makes its managed context ceiling explicit. Together they make Claude Code report and manage a `1000000`-token total context window for `claudex` without changing ordinary `claude` sessions. They do not increase an upstream model limit. The active Codex catalog may report a smaller per-model window; report that discrepancy instead of presenting the client setting as proof of upstream capacity. System instructions, tools, history, output allowance, and compaction leave less than 1M for user-provided files and prompts.

## Verify an installed profile

The standard-library verifier sends two real requests through the installed wrapper: the default Fable route and explicit Opus. Each reads a temporary random fixture, then checks the result, resolved model, tool round trip, and `contextWindow=1000000`. It disables external MCP configuration for these checks and does not print credentials.

```bash
python3 setup-claude-code-codex-bridge/scripts/verify_profile.py \
  --claudex "$HOME/cliproxyapi/claudex"
```

This is a small connectivity and tool-use check, not a near-limit context test or proof of upstream Priority processing. Validate `reasoning.effort` and `service_tier` separately through Responses metadata as described in the skill.

## Install the skill

```bash
git clone git@github.com:Whale-Dolphin/claude-code-codex-bridge.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R claude-code-codex-bridge/setup-claude-code-codex-bridge \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex after installation, then invoke it with:

```text
Use $setup-claude-code-codex-bridge to configure Fable as Astra xhigh Fast, Opus as Sol xhigh Fast, preserve [1m] on both, and verify the default and model switching.
```

## Security

This repository contains no OAuth credentials, API keys, device codes, local proxy configuration, or shell configuration copied from a real machine. The examples use placeholders and bind the proxy to `127.0.0.1` by default.

Before publishing changes, stage only the files in this repository and run a secret scan. Never add `~/.zshrc`, `~/.codex/auth.json`, `~/.cli-proxy-api/`, or a live `config.yaml`.

## Repository layout

```text
.
├── README.md
└── setup-claude-code-codex-bridge/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    └── scripts/
        └── verify_profile.py
```
