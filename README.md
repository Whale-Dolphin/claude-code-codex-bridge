# claude-code-codex-bridge

A Codex skill for installing, configuring, verifying, and troubleshooting a [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) bridge from Codex OAuth to Claude Code. The proxy and Claude client can be installed together or on different machines.

## Installation modes

The skill asks for one of three component modes before changing the machine:

| Mode | Installed here | Proxy used by local `claudex` |
| --- | --- | --- |
| `proxy-only` | CLIProxyAPI, Codex OAuth, proxy service | No local client is installed |
| `client-only` | Claude Code launchers, client profile, routectl | External URL and key supplied by the user |
| `all` | Proxy and client components | Local `http://127.0.0.1:8317` proxy |

`client-only` and `all` share `~/.config/claudex/proxy-url` plus a mode-`0600` `proxy.key`. The URL and key are kept out of shell aliases, so switching the selected proxy does not require rewriting the model profile. See [installation modes](setup-claude-code-codex-bridge/references/install-modes.md) for the exact component and security boundaries.

## What it configures

- A localhost-only CLIProxyAPI service backed by Codex OAuth in `proxy-only` and `all`
- A reusable `claudex-direct` launcher for either a local or external proxy in `client-only` and `all`
- A standard Astra route for Fable plus a standard Sol route for Opus, with explicit legacy Fast aliases still available
- Claude Code native `/fast` mapped dynamically from Opus 5 to Codex Priority processing on Sol
- A 1M Claude Code managed context profile for Fable and Opus, activated with `[1m]` model suffixes and scoped to `claudex` and `claudex-direct`
- A default official Remote Control launcher that keeps Anthropic's control plane first-party while selectively routing inference through the selected bridge
- A `600K` auto-compaction working window that preserves the `1M` profile while leaving room to summarize before the upstream limit
- A hardened user-level systemd service for a locally installed proxy
- Mode-specific model-list, standard-route, native-Fast, client, and Remote Control validation

## Default Claude Code mappings

| Claude Code label | Model | Reasoning / processing |
| --- | --- | --- |
| Fable (default) | `gpt-6-astra[1m]` | CC effort (default `xhigh`) / standard tier |
| Opus, Fast OFF | `claude-opus-5[1m]` → `gpt-5.6-sol` | CC effort (default `xhigh`) / standard tier |
| Opus, Fast ON | `claude-opus-5[1m]` → `gpt-5.6-sol` | CC effort / requested Priority |
| Sonnet | `gpt-5.6-terra` | Existing provider behavior |
| Haiku | `gpt-5.6-luna` | Existing provider behavior |
| Subagent | `gpt-6-astra[1m]` | CC-selected effort / standard tier |

Fable uses canonical Astra without a fixed Priority override; the explicit Astra Fast alias remains available for older or custom clients. Opus deliberately keeps the Claude-recognized `claude-opus-5[1m]` identity on the client side so Claude Code can emit its native `speed: "fast"` signal. routectl and CLIProxyAPI map that identity to canonical `gpt-5.6-sol`; CLIProxyAPI converts `speed: "fast"` to `service_tier: "priority"`. With Fast off, the same Opus route omits the speed field and stays standard. The bridge must not override `reasoning.effort`.

Each new `claudex` session starts with native Fast off because the launcher supplies `fastModePerSessionOptIn: true`. Use `/fast on` and `/fast off` interactively. Turning Fast on while Fable is selected makes Claude Code switch to its configured Opus identity, which routectl maps to Sol. The explicit `gpt-5.6-sol-fast` alias remains available for older clients, but Opus no longer selects it by default.

The `[1m]` suffix belongs to Claude Code-facing names; Terra and Luna remain unsuffixed, and CLIProxyAPI's aliases and canonical GPT IDs remain unsuffixed. The skill reports Priority processing as confirmed only when upstream response metadata confirms it. A request carrying native Fast is not proof that the Codex OAuth upstream granted Priority; the current live validation returned `service_tier: standard` for both modes.

## Native Fast routing

Claude Code only emits its native Fast wire fields for model identities it recognizes as Fast-capable Opus. Mapping Opus directly to `gpt-5.6-sol[1m]` makes the `/fast` UI toggle appear, but the request omits both `speed: "fast"` and the `fast-mode-2026-02-01` beta. The bridge therefore uses a two-stage identity boundary:

```text
Claude Code: claude-opus-5[1m]
        ↓ routectl / CLIProxy alias
Codex OAuth: gpt-5.6-sol
        ↓ only when /fast is on
service_tier: priority
```

`CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK=1` bypasses only Claude Code's first-party availability probe for this gateway path. It does not force the upstream to honor Priority. See the official [Claude Code Fast mode documentation](https://code.claude.com/docs/en/fast-mode).

## Effort and ultracode

CC sends adaptive thinking with `output_config.effort`; CLIProxyAPI translates it into Codex `reasoning.effort`. The default is `xhigh`, not a server-side lock. Change a running session with `/effort max`, or launch `claudex --effort max` (append `--model opus` for Sol).

| CC selection | Codex display label | Upstream effort |
| --- | --- | --- |
| `low` | Light | `low` |
| `medium` | Medium | `medium` |
| `high` | High | `high` |
| `xhigh` | Extra High | `xhigh` |
| `max` | Max | `max` |
| `ultracode` | Not Codex Ultra | `xhigh`, plus CC-owned dynamic workflows |

`ultracode` is a CC mode, not an upstream model effort. CC remains responsible for workflows, tools, and subagents; the bridge does not start a Codex agent or turn on Codex Ultra. Workflow availability depends on CC settings and model capabilities. Never report it as active based only on an `xhigh` request: verify the CC activation reminder and Workflow tool. Do not set a fixed `CLAUDE_CODE_EFFORT_LEVEL` in the wrapper, because it can override session choices and disable ultracode orchestration.

These are parameter mappings, not equal token/compute budgets across models. See the official [CC effort and ultracode documentation](https://code.claude.com/docs/en/model-config#adjust-effort-level) and [Codex model controls](https://learn.chatgpt.com/docs/models). Legacy fixed `thinking.budget_tokens` is a separate conversion path; use adaptive thinking for five-level alignment.

## 1M context profile with 600K auto-compaction

The skill combines Claude Code-facing `[1m]` suffixes on standard Astra and the Opus 5 client identity with this client-side context setting inside both launch paths:

```zsh
CLAUDE_CODE_MAX_CONTEXT_TOKENS="1000000"
claude --remote-control "Claudex Remote Control" \
  --model fable --effort xhigh --autocompact 600k
```

The suffix activates Claude Code's 1M model profile, while the environment variable makes its managed context ceiling explicit. Together they make Claude Code report and manage a `1000000`-token total context window for `claudex` and `claudex-direct` without changing ordinary `claude` sessions. They do not increase an upstream model limit. The active Codex catalog may report a smaller per-model window; report that discrepancy instead of presenting the client setting as proof of upstream capacity. System instructions, tools, history, output allowance, and compaction leave less than 1M for user-provided files and prompts.

`--autocompact 600k` keeps that 1M profile but tells Claude Code to compact as the working context approaches 600K instead of waiting near the 1M ceiling. It is a safety margin for summary generation and output, not a change to the upstream model's physical context limit, and it does not guarantee compaction at exactly token 600,000. Existing sessions must be restarted or resumed with the flag before the new threshold applies.

## Verify an installed profile

The standard-library profile verifier sends two real requests through the installed wrapper: the default Fable route and explicit Opus. Each reads a temporary random fixture, then checks the result, resolved model, tool round trip, and `contextWindow=1000000`. The native Fast verifier separately captures Claude Code's wire request and requires Fast OFF to omit `speed`, while Fast ON sends `speed: "fast"` plus the beta header. Both disable external MCP configuration and do not print credentials.

```bash
python3 setup-claude-code-codex-bridge/scripts/verify_profile.py \
  --claudex "$HOME/.local/bin/claudex-direct"
python3 setup-claude-code-codex-bridge/scripts/verify_fast.py
```

Repeat with `--effort max` to verify tool use and 1M accounting at the highest native effort. For the full client-wire, upstream-metadata, and E2E test matrix, see [verification](setup-claude-code-codex-bridge/references/verification.md). These are small connectivity/contract checks, not quality benchmarks, near-limit context tests, or proof of upstream Priority processing.

## Default official Remote Control

Claude Code rejects official Remote Control when `ANTHROPIC_BASE_URL` is custom. The default `claudex` entrypoint therefore leaves Claude's first-party URL and subscription authentication untouched, then uses routectl's loopback-only selective MITM proxy to send only inference paths to the selected local or external CLIProxyAPI endpoint. The included launcher removes conflicting base URL, auth, provider, proxy, disabled-traffic, and fixed-effort variables before starting the official Remote Control session. `claudex-direct` preserves the custom-base-url path as an explicit fallback.

The selective Remote Control path was previously validated end to end with Astra Fast. The current Fable default is standard Astra, so that route still requires the deployment/mobile gate after installation. Opus→standard Sol and Opus native Fast→Sol Priority-request paths were validated through the same official-base-url proxy path with managed context `1000000`; the upstream response reported the standard tier, so a Priority grant remains unconfirmed.

This is security-sensitive because the reviewed local process terminates TLS for `api.anthropic.com` and can see the full-scope Claude session token. Both routectl listeners remain on loopback; in `all`, CLIProxyAPI does too. The CA is scoped to one Claude process, and prompt/body logging is disabled. Read the pinned source, configuration, rollback steps, security boundary, and full test matrix in [official Remote Control compatibility](setup-claude-code-codex-bridge/references/remote-control.md) before enabling it.

### Mobile model labels and switching

The official Claude mobile app and `claude.ai/code` keep their built-in Claude-family labels; the bridge cannot replace that picker with Codex model names. A Remote Control session launched as Fable presents `gpt-6-astra[1m]`, while one launched as Opus presents `claude-opus-5[1m]` to Claude Code and routes inference to `gpt-5.6-sol`. The phone can therefore show `Fable 5.1` or `Opus 5` even though routectl and CLIProxyAPI are serving Astra or Sol. Verify routectl/CLIProxy evidence rather than treating the mobile label as the upstream model name.

Running `claudex` creates a Remote Control session named `Claudex Remote Control`. For reliable phone-only selection between Astra and Sol, start two explicitly named sessions:

```bash
scripts/claudex-remote-control "My workstation · Astra"
scripts/claudex-remote-control "My workstation · Sol" --model opus
```

Do not rely on the in-session mobile model picker for custom model IDs. The official picker may not recognize the mapped ID or may defer a change until a phone-originated message, and `/model` in a conversation with prior output requires a local confirmation before Claude Code re-reads the uncached history. The two-session approach avoids that control-plane ambiguity, but the sessions have separate conversation histories. See the [mobile behavior and verification notes](setup-claude-code-codex-bridge/references/remote-control.md#mobile-model-labels-and-reliable-switching).

## Install the skill

```bash
git clone git@github.com:Whale-Dolphin/claude-code-codex-bridge.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R claude-code-codex-bridge/setup-claude-code-codex-bridge \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex after installation, then invoke it with:

```text
Use $setup-claude-code-codex-bridge to install the bridge. Ask me to choose proxy-only, client-only, or all first; for client-only, collect the external proxy URL and key securely. Preserve Fable/standard Astra, Opus/standard Sol, native /fast to Sol Priority, [1m], effort, and Remote Control behavior, then verify the selected components.
```

## Security

This repository contains no OAuth credentials, API keys, device codes, local proxy configuration, or shell configuration copied from a real machine. The examples use placeholders and bind locally installed services to `127.0.0.1` by default. External client profiles should use HTTPS across untrusted networks.

Before publishing changes, stage only the files in this repository and run a secret scan. Never add `~/.zshrc`, `~/.codex/auth.json`, `~/.cli-proxy-api/`, or a live `config.yaml`.

## Repository layout

```text
.
├── README.md
└── setup-claude-code-codex-bridge/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── references/
    │   ├── install-modes.md
    │   ├── remote-control.md
    │   └── verification.md
    └── scripts/
        ├── claudex-direct
        ├── claudex-remote-control
        ├── verify_effort.py
        ├── verify_fast.py
        └── verify_profile.py
```
