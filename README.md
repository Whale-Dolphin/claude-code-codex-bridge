# claude-code-codex-bridge

A Codex skill for installing, configuring, verifying, and troubleshooting a local [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) bridge from Codex OAuth to Claude Code.

## What it configures

- A localhost-only CLIProxyAPI service backed by Codex OAuth
- A separate `gpt-5.6-sol-fast` client alias that routes to `gpt-5.6-sol` and requests Priority processing
- Claude Code `/model` mappings for GPT-5.6 models
- A hardened user-level systemd service
- End-to-end model-list, normal-route, Fast-route, and shell validation

## Default Claude Code mappings

| Claude Code label | Model |
| --- | --- |
| Fable | `gpt-5.6-sol-fast` |
| Opus | `gpt-5.6-sol` |
| Sonnet | `gpt-5.6-terra` |
| Haiku | `gpt-5.6-luna` |
| Subagent | `gpt-5.6-sol` |

The Fast entry is a client-visible alias, not a distinct upstream model. The skill reports Priority processing as confirmed only when response metadata confirms it.

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
