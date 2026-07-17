---
name: setup-claude-code-codex-bridge
description: "Install, upgrade, configure, verify, and troubleshoot a localhost CLIProxyAPI bridge that exposes Codex OAuth models to Claude Code through an Anthropic-compatible endpoint. Use when setting up or repairing Claude Code access to GPT-5.6 Sol, Terra, or Luna; creating a separate gpt-5.6-sol-fast alias with Priority service tier; managing Codex device login or a user systemd service; editing shell model mappings; limiting 272K context accounting to claudex; or validating Claude Code /model switching and end-to-end requests."
---

# Setup Claude Code Codex Bridge

Bridge a ChatGPT Codex OAuth session into Claude Code through a local CLIProxyAPI server. Preserve existing configuration, keep the listener private to localhost, and verify each layer before declaring success.

## Operating rules

- Inspect the host before changing it. Reuse a working install, config, auth directory, service, and shell block when present.
- Preserve unrelated user changes. Back up an existing config before restructuring it, and patch only the relevant shell block.
- Never print, copy into chat, or commit OAuth files, API keys, management secrets, or shell history containing credentials.
- Bind the proxy to `127.0.0.1` unless the user explicitly authorizes network exposure.
- Use model IDs returned by the current OAuth catalog. Do not infer access from public model documentation.
- Match Claude Code context accounting to the active OAuth catalog, never above it. When the catalog reports `272000`, set `CLAUDE_CODE_MAX_CONTEXT_TOKENS="272000"` inside the `claudex` alias only; do not export it globally.
- Do not add `[1m]` or another context suffix to Codex model IDs. A client-side setting cannot enlarge the upstream model window.
- Describe 272K as the total managed context window, not 272K of file or prompt input. System instructions, tools, history, output allowance, and compaction consume part of it.
- Treat `gpt-5.6-sol-fast` as a client-visible alias for `gpt-5.6-sol`, not as a separate upstream model.
- Request Priority processing for the Fast alias, but do not claim the upstream honored it unless response metadata confirms that tier.
- Request approval before downloading binaries, opening a browser, changing services outside the user scope, or performing any other action that requires elevated access.

## Default paths

Use these paths unless the user already has a different layout:

```text
~/cliproxyapi/cli-proxy-api       active binary
~/cliproxyapi/<version>/          extracted version for rollback
~/cliproxyapi/config.yaml         active configuration
~/.cli-proxy-api/                 OAuth credential directory
~/.config/systemd/user/cliproxyapi.service
~/.zshrc                          Claude Code alias on zsh
```

## 1. Discover the current state

Run read-only checks first:

```bash
uname -s
uname -m
command -v claude
claude --version
test -x "$HOME/cliproxyapi/cli-proxy-api" && "$HOME/cliproxyapi/cli-proxy-api" --help
test -f "$HOME/cliproxyapi/config.yaml" && rg -n '^(host|port|auth-dir|oauth-model-alias|payload):' "$HOME/cliproxyapi/config.yaml"
rg -n -C 4 'alias claudex|ANTHROPIC_DEFAULT_(FABLE|OPUS|SONNET|HAIKU)_MODEL' "$HOME/.zshrc" 2>/dev/null
```

Locate any user service with `rg --files ~/.config/systemd/user`. Check service status and logs when a user systemd bus is available. Do not assume a failed `systemctl --user` call means the proxy itself is broken; restricted shells and containers may not expose the user bus.

## 2. Install or upgrade CLIProxyAPI

Use the official `router-for-me/CLIProxyAPI` release matching the host OS and architecture:

- Releases: `https://github.com/router-for-me/CLIProxyAPI/releases/latest`
- Configuration reference: `https://help.router-for.me/configuration/options`

Resolve the release dynamically rather than hard-coding a version. On Linux, map `x86_64` to `amd64` and `aarch64` or `arm64` to `arm64`, then select the corresponding release archive. Download to a temporary directory, verify a published checksum when available, and extract into `~/cliproxyapi/<version>/`.

Keep rollback possible:

1. Leave `config.yaml` and `~/.cli-proxy-api/` untouched during upgrades.
2. Retain the previous versioned directory.
3. Install or copy the new executable to `~/cliproxyapi/cli-proxy-api` with mode `0755` only after extraction succeeds.
4. Record the active version in `~/cliproxyapi/version.txt`.
5. Run `cli-proxy-api --help` and read its version banner before restarting the service.

Do not pipe an unreviewed third-party installer directly into a shell. Prefer the official release archive and inspect its asset name first.

## 3. Configure the local bridge

Generate a random local proxy key and keep it consistent between `config.yaml` and the Claude Code alias. Do not reuse a real provider credential.

Create or merge the following fields into `~/cliproxyapi/config.yaml`:

```yaml
host: "127.0.0.1"
port: 8317

tls:
  enable: false

remote-management:
  allow-remote: false
  secret-key: ""
  disable-control-panel: true

auth-dir: "~/.cli-proxy-api"

api-keys:
  - "<random-local-proxy-key>"

debug: false
logging-to-file: false
usage-statistics-enabled: false
request-retry: 3
ws-auth: true

oauth-model-alias:
  codex:
    - name: "gpt-5.6-sol"
      alias: "gpt-5.6-sol-fast"
      fork: true

payload:
  override:
    - models:
        - name: "gpt-5.6-sol-fast"
          protocol: "codex"
      params:
        service_tier: "priority"
```

Keep `fork: true` so both `gpt-5.6-sol` and `gpt-5.6-sol-fast` remain visible. Use `payload.override` because the Fast route must overwrite any conflicting client value.

Validate the YAML with an available parser before restarting. Never print the unredacted file in tool output.

## 4. Connect the Codex OAuth account

Create the auth directory with user-only permissions, then start device login:

```bash
mkdir -p "$HOME/.cli-proxy-api"
chmod 700 "$HOME/.cli-proxy-api"
"$HOME/cliproxyapi/cli-proxy-api" --config "$HOME/cliproxyapi/config.yaml" --codex-device-login
```

Give the user the displayed verification URL and device code. Wait for confirmation, then let the command finish. If the code expires, rerun the login command to generate a new code; do not reuse the expired code.

Verify only that a Codex auth file exists and has restrictive permissions. Do not read its contents into the conversation.

## 5. Run the proxy as a user service

On Linux with user systemd, create `~/.config/systemd/user/cliproxyapi.service`:

```ini
[Unit]
Description=CLIProxyAPI local Codex bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/cliproxyapi
ExecStart=%h/cliproxyapi/cli-proxy-api --config %h/cliproxyapi/config.yaml
Restart=on-failure
RestartSec=5
Environment=HOME=%h
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.cli-proxy-api

[Install]
WantedBy=default.target
```

Then run:

```bash
systemctl --user daemon-reload
systemctl --user enable --now cliproxyapi.service
systemctl --user status cliproxyapi.service --no-pager
```

If user systemd is unavailable, run the same `ExecStart` command in a supervised terminal or another user-level process manager. Do not silently fall back to a root service.

## 6. Map Claude Code models

Patch one clearly labeled `claudex` block in the active shell startup file. Remove an older copy before adding a replacement so repeated runs stay idempotent.

Before patching, inspect the current Codex OAuth catalog. Use `272000` below only when that catalog reports a 272K maximum for the selected models. Keep the variable inline in the alias so `claudex` receives it while ordinary `claude` sessions remain unchanged.

For zsh, use:

```zsh
# Claude Code /model mapping for the local Codex bridge:
# Fable = gpt-5.6-sol-fast, Opus = gpt-5.6-sol,
# Sonnet = gpt-5.6-terra, Haiku = gpt-5.6-luna.
unalias claudex 2>/dev/null
alias claudex='env -u CLAUDE_CODE_USE_BEDROCK \
        -u CLAUDE_CODE_SKIP_BEDROCK_AUTH \
        -u CLAUDE_CODE_USE_VERTEX \
        -u CLAUDE_CODE_USE_FOUNDRY \
        ANTHROPIC_BASE_URL="http://127.0.0.1:8317" \
        ANTHROPIC_AUTH_TOKEN="<random-local-proxy-key>" \
        ANTHROPIC_API_KEY="" \
        ANTHROPIC_DEFAULT_FABLE_MODEL="gpt-5.6-sol-fast" \
        ANTHROPIC_DEFAULT_OPUS_MODEL="gpt-5.6-sol" \
        ANTHROPIC_DEFAULT_SONNET_MODEL="gpt-5.6-terra" \
        ANTHROPIC_DEFAULT_HAIKU_MODEL="gpt-5.6-luna" \
        CLAUDE_CODE_SUBAGENT_MODEL="gpt-5.6-sol" \
        CLAUDE_CODE_MAX_CONTEXT_TOKENS="272000" \
        CLAUDE_CODE_ALWAYS_ENABLE_EFFORT="1" \
        CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY="3" \
        ENABLE_TOOL_SEARCH="false" \
        claude --model gpt-5.6-sol'
```

Replace the placeholder with the same local proxy key used in `config.yaml`. Preserve every unrelated alias and environment variable in the shell file.

## 7. Verify end to end

Verify in increasing order of cost:

1. Validate shell syntax with `zsh -n ~/.zshrc` and inspect the expanded alias without printing unrelated credentials. Confirm `CLAUDE_CODE_MAX_CONTEXT_TOKENS=272000` is present in `claudex`, while a fresh ordinary shell leaves the variable unset.
2. Confirm the service is listening only on `127.0.0.1:8317`.
3. Query `GET /v1/models` with the local proxy key and confirm these client-visible IDs are present:
   - `gpt-5.6-sol`
   - `gpt-5.6-sol-fast`
   - `gpt-5.6-terra`
   - `gpt-5.6-luna`
4. Send a minimal non-interactive request through normal Sol and require an exact short response.
5. Send the same request through `gpt-5.6-sol-fast`. Confirm routing success, but describe Priority activation as unconfirmed unless returned metadata reports the requested tier.
6. Start `claudex`, run `/model`, and confirm the Fable, Opus, Sonnet, and Haiku entries resolve to the intended IDs.

Example minimal checks after loading the shell config:

```zsh
source ~/.zshrc
claudex -p --model gpt-5.6-sol 'Reply with exactly SOL_OK'
claudex -p --model gpt-5.6-sol-fast --output-format json 'Reply with exactly FAST_OK'
```

Verify Claude Code's effective accounting with a small JSON request:

```zsh
claudex -p --model gpt-5.6-sol --tools "" --no-session-persistence \
  --output-format json 'Reply with exactly CONTEXT_OK' |
  jq '{result, models: (.modelUsage | to_entries | map({model: .key, contextWindow: .value.contextWindow}))}'
```

Require `contextWindow: 272000` before reporting success. The setting changes Claude Code's management and auto-compaction ceiling for this invocation; it does not prove that 272K tokens of user files fit in one request or raise a smaller upstream limit. Keep verification prompts small unless the user explicitly requests a costly near-limit test.

## 8. Modify mappings safely

- To change Claude Code's Fable, Opus, Sonnet, Haiku, or Subagent selection, patch only the corresponding environment variable and the trailing default `--model` when requested.
- To expose another client-visible alias, add it under `oauth-model-alias.codex`, keep the canonical upstream name in `name`, and decide explicitly whether `fork` should preserve the original.
- To attach request behavior to an alias, add a narrowly matched `payload` rule with `protocol: "codex"`.
- Restart or reload the proxy, refresh the shell, and repeat the model-list plus minimal-request checks after every mapping change.

## Troubleshooting

- **Expired device code:** rerun `--codex-device-login` and use the new code.
- **401 from the local endpoint:** make the proxy key in Claude Code match one entry under `api-keys`.
- **Unknown model:** inspect `/v1/models`, confirm the OAuth account exposes the canonical model, and verify the alias is under the `codex` channel.
- **Alias replaces the original:** set `fork: true` and restart or reload the proxy.
- **Fast request succeeds but reports the standard tier:** the alias routing works, but the upstream did not confirm Priority processing; report that limitation accurately.
- **Claude Code shows stale mappings:** open a new shell or source the startup file, then restart Claude Code. If Claude Code starts from a GUI or a different shell, configure that launch environment because it may not read `.zshrc`.
- **Claude Code still reports 200K:** confirm the 272K environment variable is inside the expanded `claudex` alias, start a fresh shell, and repeat the JSON `modelUsage` check. Do not work around the mismatch with a `[1m]` model suffix.
- **Service repeatedly restarts:** inspect `journalctl --user -u cliproxyapi.service`, validate YAML, verify binary permissions, and confirm the auth directory is writable under the service sandbox.
- **OAuth model list changes:** treat the latest catalog as authoritative and update mappings only to IDs the account currently exposes.

## Handoff

Report the installed version, active paths, service state, exposed model IDs, shell mapping, and minimal request results. State whether Fast routing merely succeeded or whether Priority processing was actually confirmed. Never include credentials or OAuth file contents.
