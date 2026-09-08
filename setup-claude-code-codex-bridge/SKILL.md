---
name: setup-claude-code-codex-bridge
description: "Install, upgrade, configure, and verify a CLIProxyAPI bridge from Codex OAuth to Claude Code. Use for claudex Fable/Astra and Opus/Sol Fast mappings, CC effort alignment and ultracode, [1m] context, login, service setup, and official Remote Control compatibility."
---

# Setup Claude Code Codex Bridge

Bridge a ChatGPT Codex OAuth session into Claude Code through a local CLIProxyAPI server. The profile launches Fable as Astra Fast and maps Opus to Sol Fast, both with `[1m]`. Default to `xhigh` but follow CC effort changes; preserve CC-owned ultracode workflows. Preserve existing configuration and explicitly authorized network exposure, and verify each layer before declaring success.

## Operating rules

- Inspect the host before changing it. Reuse a working install, config, auth directory, service, and shell block when present.
- Preserve unrelated user changes. Back up an existing config before restructuring it, and patch only the relevant shell block.
- Never print, copy into chat, or commit OAuth files, API keys, management secrets, or shell history containing credentials.
- Bind the proxy to `127.0.0.1` unless the user explicitly authorizes network exposure.
- Use model IDs returned by the current OAuth catalog. Do not infer access from public model documentation.
- Inspect the active OAuth catalog before changing context accounting. This profile appends `[1m]` to the Claude Code-facing Astra Fast and Sol Fast names and sets `CLAUDE_CODE_MAX_CONTEXT_TOKENS="1000000"` inside the `claudex` alias only; do not export it globally. Keep Terra and Luna unsuffixed.
- Keep CLIProxyAPI's canonical OAuth model names and `/v1/models` entries unsuffixed. The `[1m]` suffix belongs only to Claude Code-facing mappings. If the catalog reports a smaller per-model maximum, report the discrepancy and describe 1M as client-side management rather than proven upstream capacity.
- Describe 1M as the total managed context window, not 1M of file or prompt input. System instructions, tools, history, output allowance, and compaction consume part of it.
- Treat `gpt-6-astra-fast` and `gpt-5.6-sol-fast` as client-visible aliases for `gpt-6-astra` and `gpt-5.6-sol`, respectively, not as separate upstream models.
- Request Priority processing for both Fast aliases, but do not override `reasoning.effort`: CC must control it. Remove the old forced `xhigh` rule when upgrading this profile. Do not claim the upstream honored Priority unless response metadata confirms that tier.
- CC `low`, `medium`, `high`, `xhigh`, and `max` map to the same Codex API values. Codex displays `low` as Light and `xhigh` as Extra High. CC `ultracode` sends `xhigh` plus CC-owned dynamic workflows, not Codex `ultra`; never transmit `ultracode` as an API effort or claim Codex agent orchestration is running.
- Official Remote Control does not accept a custom `ANTHROPIC_BASE_URL`. Use the reviewed routectl selective-MITM path only when the user asks for official Remote Control; keep Claude's base URL and auth variables unset, keep all three listeners on loopback, and read [references/remote-control.md](references/remote-control.md) before acting.
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
    - name: "gpt-6-astra"
      alias: "gpt-6-astra-fast"
      fork: true
    - name: "gpt-5.6-sol"
      alias: "gpt-5.6-sol-fast"
      fork: true

payload:
  override:
    - models:
        - name: "gpt-6-astra-fast"
          protocol: "codex"
        - name: "gpt-5.6-sol-fast"
          protocol: "codex"
      params:
        service_tier: "priority"
```

Keep `fork: true` on both aliases so Astra and Sol remain available under their canonical IDs. Use `payload.override` only for the Fast service tier. Do not add a default or override reasoning rule: the CC launcher provides the default, and the translator preserves explicit CC effort. Match only the two aliases, so explicit canonical requests and Terra/Luna retain their existing behavior.

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

Before patching, inspect the current Codex OAuth catalog. This profile uses `[1m]` suffixes on Astra Fast and Sol Fast plus `1000000` for Claude Code's client-side managed window. Terra and Luna stay unsuffixed. When the catalog advertises a smaller maximum for a selected model, surface that mismatch and do not claim the settings raise the upstream limit. Keep the variable inline in the alias so `claudex` receives it while ordinary `claude` sessions remain unchanged.

For zsh, use:

```zsh
# Claude Code /model mapping for the local Codex bridge:
# Fable (default) = gpt-6-astra-fast[1m], Opus = gpt-5.6-sol-fast[1m]; default effort xhigh.
# Sonnet = gpt-5.6-terra, Haiku = gpt-5.6-luna.
unalias claudex 2>/dev/null
alias claudex='env -u CLAUDE_CODE_USE_BEDROCK \
        -u CLAUDE_CODE_SKIP_BEDROCK_AUTH \
        -u CLAUDE_CODE_USE_VERTEX \
        -u CLAUDE_CODE_USE_FOUNDRY \
        ANTHROPIC_BASE_URL="http://127.0.0.1:8317" \
        ANTHROPIC_AUTH_TOKEN="<random-local-proxy-key>" \
        ANTHROPIC_API_KEY="" \
        ANTHROPIC_DEFAULT_FABLE_MODEL="gpt-6-astra-fast[1m]" \
        ANTHROPIC_DEFAULT_OPUS_MODEL="gpt-5.6-sol-fast[1m]" \
        ANTHROPIC_DEFAULT_SONNET_MODEL="gpt-5.6-terra" \
        ANTHROPIC_DEFAULT_HAIKU_MODEL="gpt-5.6-luna" \
        CLAUDE_CODE_SUBAGENT_MODEL="gpt-6-astra-fast[1m]" \
        CLAUDE_CODE_MAX_CONTEXT_TOKENS="1000000" \
        CLAUDE_CODE_ALWAYS_ENABLE_EFFORT="1" \
        CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY="3" \
        ENABLE_TOOL_SEARCH="false" \
        claude --model fable --effort xhigh'
```

Replace the placeholder with the same local proxy key used in `config.yaml`. Preserve every unrelated alias and environment variable in the shell file.

The trailing `--model fable` selects the Fable label itself; its environment mapping resolves to Astra Fast. `--effort xhigh` is a launch default, not an upstream override. In an executable wrapper, append user arguments after these defaults so `claudex --effort max` can override them. In a running interactive session use `/effort low`, `/effort medium`, `/effort high`, `/effort xhigh`, or `/effort max`.

Do not hard-code `CLAUDE_CODE_EFFORT_LEVEL`: it can override session choices and prevent ultracode workflows. If the user already supplies it, report the precedence rather than silently removing their setting. CC should send `thinking.type: adaptive` and `output_config.effort`; do not substitute a fixed `MAX_THINKING_TOKENS` budget for this five-level contract.

Use `claudex --effort ultracode` or interactive `/effort ultracode` to keep CC's native `xhigh` plus workflow mode (requires CC 2.1.203+ and enabled dynamic workflows). Do not force-enable workflows against user settings. Confirm the actual request has the ultracode activation reminder and Workflow tool; a successful `xhigh` response alone proves neither workflow activation nor delegation. The bridge invokes model APIs, not a Codex agent. See [CC effort documentation](https://code.claude.com/docs/en/model-config#adjust-effort-level).

## 7. Verify end to end

Verify in increasing order of cost:

1. Validate shell syntax with `zsh -n ~/.zshrc` and inspect only non-secret fields of the alias or wrapper. Confirm Fable is Astra Fast, Opus is Sol Fast, both end in `[1m]`, and the launcher selects `--model fable --effort xhigh`. Terra and Luna stay unsuffixed, and `CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000` is scoped to `claudex`.
2. Confirm the listener matches the authorized exposure: localhost by default, or the user's explicitly selected network interface and firewall scope.
3. Query `GET /v1/models` with the local proxy key and confirm these client-visible IDs are present:
   - `gpt-6-astra`
   - `gpt-6-astra-fast`
   - `gpt-5.6-sol`
   - `gpt-5.6-sol-fast`
   - `gpt-5.6-terra`
   - `gpt-5.6-luna`
4. Send a minimal request through plain `claudex` with no model override and require an exact response plus `gpt-6-astra-fast[1m]` in the JSON model usage. This verifies the default Fable mapping, not just an explicitly selected model ID.
5. Repeat through `claudex --model opus` and require `gpt-5.6-sol-fast[1m]`. Capture the client's five effort levels and ultracode wire behavior, then send small Responses API requests to both unsuffixed Fast aliases and require the returned canonical model and `reasoning.effort` to match each requested level. Inspect `service_tier` separately and describe Priority as unconfirmed unless returned metadata reports it.
6. Start `claudex`, run `/model`, and confirm the Fable, Opus, Sonnet, and Haiku entries resolve to their intended IDs.

For the default/Opus model, Read tool round-trip, and 1M client-accounting checks, run the included standard-library verifier:

```bash
python3 scripts/verify_profile.py --claudex "$HOME/cliproxyapi/claudex"
```

Run it from this skill directory. Repeat with `--effort max` and `--effort ultracode` as appropriate. It invokes the executable wrapper directly, so pass its actual path when the install uses a different layout. For a shell-only alias, use the manual checks below and a small read-only tool request. The verifier does not establish upstream Priority or context capacity. When updating effort or ultracode behavior, read [references/verification.md](references/verification.md) for the client-wire and real-upstream tests; do not confuse either stage alone with full E2E verification.

Example minimal checks after loading the shell config:

```zsh
source ~/.zshrc
claudex -p --output-format json 'Reply with exactly ASTRA_FAST_OK'
claudex -p --model opus --output-format json 'Reply with exactly SOL_FAST_OK'
```

Verify Claude Code's effective accounting with a small JSON request:

```zsh
claudex -p --tools "" --no-session-persistence \
  --output-format json 'Reply with exactly CONTEXT_OK' |
  jq '{result, models: (.modelUsage | to_entries | map({model: .key, contextWindow: .value.contextWindow}))}'
```

Require the reported model name to retain `[1m]` and `contextWindow: 1000000` before reporting success. The settings change Claude Code's model profile, management, and auto-compaction ceiling for this invocation; they do not prove that 1M tokens of user files fit in one request or raise a smaller upstream limit. Keep verification prompts small unless the user explicitly requests a costly near-limit test.

## 8. Add official Remote Control compatibility when requested

Do not try to launch Remote Control through the ordinary `claudex` alias: its custom base URL makes Claude Code reject the feature. The verified optional path uses routectl as a process-scoped HTTPS proxy. It re-injects only Anthropic inference paths into a loopback router backed by CLIProxyAPI, while Anthropic control-plane traffic remains first-party.

Read [references/remote-control.md](references/remote-control.md) completely before installing routectl or generating its CA. Pin and review the documented source commit, keep CLIProxyAPI on `127.0.0.1:8317`, routectl HTTP on `127.0.0.1:8787`, and routectl MITM on `127.0.0.1:8443`. Leave routectl listener auth off for this single-user loopback path and store the CLIProxy key in a mode-0600 file referenced by `file://`; never embed it in TOML, the launcher, logs, or chat.

Launch with the included script after routectl is healthy:

```bash
ROUTECTL_CONFIG="$HOME/.config/routectl/config.toml" \
  scripts/claudex-remote-control "My workstation"
```

The launcher must unset `ANTHROPIC_BASE_URL`, Anthropic key/token variables, provider flags, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, and fixed effort overrides. It reads the proxy and CA from `routectl rc env` without `eval`, refuses a non-loopback proxy, and scopes all variables to the Claude process.

Do not declare success from an active `/remote-control` banner alone. Send a random exact-response prompt from the official phone or web client, observe the same message and response in the local session, require a new CLIProxyAPI `/v1/messages` request, and confirm routectl selected Astra Fast. Repeat a normal official-base-url CLI request through the same proxy for Opus/Sol Fast at `max`. Claude versions may display the Fast model with or without `[1m]`; require the intended route plus `contextWindow: 1000000`.

## 9. Modify mappings safely

- To change Claude Code's Fable, Opus, Sonnet, Haiku, or Subagent selection, patch only the corresponding environment variable and the trailing default `--model` when requested. This profile uses Fable/Astra Fast by default and Opus/Sol Fast, both with `[1m]` and CC-selected effort (launch default `xhigh`); keep Terra and Luna unsuffixed unless their upstream context support is separately verified.
- To expose another client-visible alias, add it under `oauth-model-alias.codex`, keep the canonical upstream name in `name`, and decide explicitly whether `fork` should preserve the original.
- To attach request behavior to an alias, add a narrowly matched `payload` rule with `protocol: "codex"`.
- Restart or reload the proxy, refresh the shell, and repeat the model-list plus minimal-request checks after every mapping change.

## Troubleshooting

- **Expired device code:** rerun `--codex-device-login` and use the new code.
- **401 from the local endpoint:** make the proxy key in Claude Code match one entry under `api-keys`.
- **Unknown model:** inspect `/v1/models`, confirm the OAuth account exposes the unsuffixed canonical model, and verify the alias is under the `codex` channel. Keep `[1m]` out of the CLIProxyAPI OAuth alias configuration and off Terra/Luna mappings.
- **Alias replaces the original:** set `fork: true` on both Fast aliases and restart or reload the proxy.
- **Fast route stays at xhigh after CC changes effort:** remove the legacy `"reasoning.effort": "xhigh"` payload override while preserving the Priority rule. Inspect `CLAUDE_CODE_EFFORT_LEVEL` precedence and capture CC's `thinking.type` and `output_config.effort`. Verify upstream metadata rather than inferring effort from the model's answer.
- **Ultracode only behaves like xhigh:** check the CC version, workflow setting, model capability detection, environment effort override, and activation reminder. Report disabled workflows honestly; do not rewrite the upstream effort to `ultra` as a workaround.
- **Fast request succeeds but reports the standard tier:** the alias routing works, but the upstream did not confirm Priority processing; report that limitation accurately.
- **Claude Code shows stale mappings:** open a new shell or source the startup file, then restart Claude Code. If Claude Code starts from a GUI or a different shell, configure that launch environment because it may not read `.zshrc`.
- **Claude Code still reports less than 1M:** confirm both the `[1m]` suffix and `1000000` environment variable are present in the expanded `claudex` alias, start a fresh shell, and repeat the JSON `modelUsage` check.
- **Remote Control says custom base URL is unsupported:** do not spoof first-party mode or add more auth variables. Stop ordinary `claudex`, verify the routectl service and CA, then use `scripts/claudex-remote-control`; see [references/remote-control.md](references/remote-control.md).
- **Remote Control starts but inference reaches Anthropic:** verify the Claude child has no custom base/auth variables, the process has routectl's `HTTPS_PROXY` and CA, and the routectl aliases target the local CLIProxy Fast models. Require a CLIProxy request-count increase and routectl model evidence.
- **Service repeatedly restarts:** inspect `journalctl --user -u cliproxyapi.service`, validate YAML, verify binary permissions, and confirm the auth directory is writable under the service sandbox.
- **OAuth model list changes:** treat the latest catalog as authoritative and update mappings only to IDs the account currently exposes.

## Handoff

Report the installed version, active paths, service state, exposed model IDs, shell mapping, and minimal request results. State whether Fast routing merely succeeded or whether Priority processing was actually confirmed. Never include credentials or OAuth file contents.
