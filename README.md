# claude-code-codex-bridge

A Codex skill for installing, configuring, verifying, and troubleshooting a local [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) bridge from Codex OAuth to Claude Code.

## What it configures

- A localhost-only CLIProxyAPI service backed by Codex OAuth
- A separate `gpt-5.6-sol-fast` client alias that routes to `gpt-5.6-sol` and requests Priority processing
- Claude Code `/model` mappings for GPT-5.6 models
- A 1M Claude Code managed context profile for Sol, activated with `[1m]` model suffixes and scoped only to `claudex`
- A hardened user-level systemd service
- End-to-end model-list, normal-route, Fast-route, and shell validation

## Default Claude Code mappings

| Claude Code label | Model |
| --- | --- |
| Fable | `gpt-5.6-sol-fast[1m]` |
| Opus | `gpt-5.6-sol[1m]` |
| Sonnet | `gpt-5.6-terra` |
| Haiku | `gpt-5.6-luna` |
| Subagent | `gpt-5.6-sol[1m]` |

The Fast entry is a client-visible alias for Sol, not a distinct upstream model. The `[1m]` suffix is used only on the Claude Code-facing Sol and Sol Fast names; Terra and Luna remain unsuffixed. CLIProxyAPI continues to expose and route canonical unsuffixed model IDs. The skill reports Priority processing as confirmed only when response metadata confirms it.

## 1M context management

The skill combines Claude Code-facing `[1m]` suffixes on Sol and Sol Fast with this client-side context setting inside the `claudex` alias:

```zsh
CLAUDE_CODE_MAX_CONTEXT_TOKENS="1000000"
```

The suffix activates Claude Code's 1M model profile, while the environment variable makes its managed context ceiling explicit. Together they make Claude Code report and manage a `1000000`-token total context window for `claudex` without changing ordinary `claude` sessions. They do not increase an upstream model limit. The active Codex catalog may report a smaller per-model window; report that discrepancy instead of presenting the client setting as proof of upstream capacity. System instructions, tools, history, output allowance, and compaction leave less than 1M for user-provided files and prompts.

## Install the skill

```bash
git clone git@github.com:Whale-Dolphin/claude-code-codex-bridge.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R claude-code-codex-bridge/setup-claude-code-codex-bridge \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex after installation, then invoke it with:

```text
Use $setup-claude-code-codex-bridge to install or update the local bridge and verify Claude Code model switching.
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
    └── agents/
        └── openai.yaml
```
