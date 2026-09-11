---
name: setup-claude-code-codex-bridge
description: "Install, upgrade, configure, and verify a CLIProxyAPI bridge from Codex OAuth to Claude Code in proxy-only, client-only, or all mode. Use for local or external claudex proxy selection, Fable/standard Astra and GPT-5.6-wide Priority mappings, CC effort alignment and ultracode, [1m] context, login, service setup, and official Remote Control compatibility."
---

# Setup Claude Code Codex Bridge

Install the proxy component, the Claude Code client component, or both. A client can use CLIProxyAPI on the same machine or an existing external machine. The client profile launches Fable as standard Astra and maps Opus directly to canonical Sol, both with `[1m]`. Every canonical GPT-5.6 Sol, Terra, and Luna request asks for Priority processing. Default to `xhigh` but follow CC effort changes; preserve CC-owned ultracode workflows. Preserve existing configuration and explicitly authorized network exposure, and verify each selected layer before declaring success.

## Operating rules

- Inspect the host before changing it. Reuse a working install, config, auth directory, service, and shell block when present.
- Preserve unrelated user changes. Back up an existing config before restructuring it, and patch only the relevant shell block.
- Never print, copy into chat, or commit OAuth files, API keys, management secrets, or shell history containing credentials.
- Bind a locally installed proxy to `127.0.0.1` unless the user explicitly authorizes exact network exposure.
- Use model IDs returned by the current OAuth catalog. Do not infer access from public model documentation.
- Inspect the active OAuth catalog before changing context accounting. This profile appends `[1m]` to the Claude Code-facing standard Astra and canonical Sol names and scopes `CLAUDE_CODE_MAX_CONTEXT_TOKENS="1000000"` to the `claudex` and `claudex-direct` launchers only; do not export it globally. Keep Terra and Luna unsuffixed.
- Keep CLIProxyAPI's canonical OAuth model names and `/v1/models` entries unsuffixed. The `[1m]` suffix belongs only to Claude Code-facing mappings. If the catalog reports a smaller per-model maximum, report the discrepancy and describe 1M as client-side management rather than proven upstream capacity.
- Describe 1M as the total managed context window, not 1M of file or prompt input. System instructions, tools, history, output allowance, and compaction consume part of it.
- Treat `gpt-6-astra-fast` as an optional client-visible alias for `gpt-6-astra`, not as a separate upstream model. Opus uses canonical `gpt-5.6-sol` directly.
- Request Priority processing for every canonical `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` request and for the optional Astra Fast alias, but do not override `reasoning.effort`: CC must control it. Fable uses canonical Astra and therefore does not request Priority. In the routectl profile, use model-scoped `payload_extras` to overwrite both `service_tier` and `speed` for all three GPT-5.6 routes. Remove the old forced `xhigh` rule and the old Sol alias when upgrading this profile. Do not claim the upstream honored Priority unless response metadata confirms that tier.
- Do not accept a model-catalog `service_tiers` entry as Fast proof. For CLIProxyAPI-backed Codex OAuth, verify the deployed HTTP/SSE transport with a completed Responses result. If it reports `default`, `auto`, or omits the tier, report Fast as unavailable even though the injected request asked for Priority. Read [references/verification.md](references/verification.md) for the transport boundary.
- CC `low`, `medium`, `high`, `xhigh`, and `max` map to the same Codex API values. Codex displays `low` as Light and `xhigh` as Extra High. CC `ultracode` sends `xhigh` plus CC-owned dynamic workflows, not Codex `ultra`; never transmit `ultracode` as an API effort or claim Codex agent orchestration is running.
- Official Remote Control does not accept a custom `ANTHROPIC_BASE_URL`. The default `claudex` entrypoint must use the reviewed routectl selective-MITM path; keep the custom-base-url path available only as `claudex-direct`. Keep Claude's base URL and auth variables unset in Remote Control, keep routectl's listeners on loopback, and read [references/remote-control.md](references/remote-control.md) before acting.
- The official phone/web model picker keeps Claude-family labels and may not reliably apply a mapped custom model ID to an existing Remote Control session. Treat Fable and Opus as client labels for the configured Astra and Sol launch mappings, verify the actual route locally, and prefer separately named Astra and Sol sessions for phone-only selection. Do not claim that those sessions share conversation history.
- Request approval before downloading binaries, opening a browser, changing services outside the user scope, or performing any other action that requires elevated access.

## Default paths

Use these paths unless the user already has a different layout:

```text
~/.config/claudex/proxy-url       selected proxy base URL, without /v1
~/.config/claudex/proxy.key       selected proxy key, mode 0600
~/.local/bin/claudex-direct       custom-base-url client launcher
~/.local/bin/claudex-remote-control
~/cliproxyapi/cli-proxy-api       active binary
~/cliproxyapi/<version>/          extracted version for rollback
~/cliproxyapi/config.yaml         active configuration
~/.cli-proxy-api/                 OAuth credential directory
~/.config/systemd/user/cliproxyapi.service
~/.zshrc                          Claude Code alias on zsh
```

## 1. Choose the mode and discover the current state

Before changing anything, ask the user to choose exactly one mode:

- `proxy-only`: install or update CLIProxyAPI and its Codex OAuth service on this machine; do not install Claude Code launchers.
- `client-only`: install or update only the local `claudex` client profile and point it at an existing external proxy.
- `all`: install or update both components and point `claudex` at the local proxy.

If the user already chose a mode, use it without asking again. For `client-only`, ask for the external base URL and obtain its key through a protected key file or hidden local terminal entry; never ask the user to paste a key into chat. Read [references/install-modes.md](references/install-modes.md) completely before making changes, and run only the sections that apply to the selected mode.

Run the relevant read-only checks first:

```bash
uname -s
uname -m
command -v claude
claude --version
test -f "$HOME/.config/claudex/proxy-url" && cat "$HOME/.config/claudex/proxy-url"
test -f "$HOME/.config/claudex/proxy.key" && stat "$HOME/.config/claudex/proxy.key"
test -x "$HOME/.local/bin/claudex-direct" && head -n 1 "$HOME/.local/bin/claudex-direct"
test -x "$HOME/cliproxyapi/cli-proxy-api" && "$HOME/cliproxyapi/cli-proxy-api" --help
test -f "$HOME/cliproxyapi/config.yaml" && rg -n '^(host|port|auth-dir|oauth-model-alias|payload):' "$HOME/cliproxyapi/config.yaml"
rg -n -C 4 'alias claudex|ANTHROPIC_DEFAULT_(FABLE|OPUS|SONNET|HAIKU)_MODEL' "$HOME/.zshrc" 2>/dev/null
```

Do not run the client launcher during discovery if doing so would send a request; inspect its path and source instead. Never read or print `proxy.key`. For `proxy-only` or `all`, locate any user service with `rg --files ~/.config/systemd/user`. Check service status and logs when a user systemd bus is available. Do not assume a failed `systemctl --user` call means the proxy itself is broken; restricted shells and containers may not expose the user bus.

## 2. Install or upgrade CLIProxyAPI (`proxy-only` and `all`)

Skip sections 2 through 5 in `client-only` mode.

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

## 3. Configure the local bridge (`proxy-only` and `all`)

Generate a random local proxy key and keep it consistent between `config.yaml` and the client profile when using `all`. Do not reuse a real provider credential.

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
payload:
  override:
    - models:
        - name: "gpt-6-astra-fast"
          protocol: "codex"
        - name: "gpt-5.6-sol"
          protocol: "codex"
        - name: "gpt-5.6-terra"
          protocol: "codex"
        - name: "gpt-5.6-luna"
          protocol: "codex"
      params:
        service_tier: "priority"
```

Keep `fork: true` on the optional Astra alias so canonical Astra remains available. Use `payload.override` only for the Priority service tier. Do not add a default or override reasoning rule: the CC launcher provides the default, and the translator preserves explicit CC effort. Match the optional Astra Fast alias plus canonical Sol, Terra, and Luna, so every GPT-5.6 request asks for Priority while canonical Astra retains standard processing.

Validate the YAML with an available parser before restarting. Never print the unredacted file in tool output.

## 4. Connect the Codex OAuth account (`proxy-only` and `all`)

Create the auth directory with user-only permissions, then start device login:

```bash
mkdir -p "$HOME/.cli-proxy-api"
chmod 700 "$HOME/.cli-proxy-api"
"$HOME/cliproxyapi/cli-proxy-api" --config "$HOME/cliproxyapi/config.yaml" --codex-device-login
```

Give the user the displayed verification URL and device code. Wait for confirmation, then let the command finish. If the code expires, rerun the login command to generate a new code; do not reuse the expired code.

Verify only that a Codex auth file exists and has restrictive permissions. Do not read its contents into the conversation.

## 5. Run the proxy as a user service (`proxy-only` and `all`)

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

## 6. Install the Claude Code client (`client-only` and `all`)

Skip sections 6 and 8 in `proxy-only` mode. In `client-only`, collect the external proxy URL and key as described in [references/install-modes.md](references/install-modes.md). In `all`, use `http://127.0.0.1:8317` and the same key accepted by the local CLIProxyAPI service.

Install the included launchers and create the shared client profile:

```bash
install -d -m 0700 "$HOME/.config/claudex" "$HOME/.local/bin"
install -m 0755 scripts/claudex-direct "$HOME/.local/bin/claudex-direct"
install -m 0755 scripts/claudex-remote-control "$HOME/.local/bin/claudex-remote-control"
printf '%s\n' '<proxy-base-url>' > "$HOME/.config/claudex/proxy-url"
chmod 0600 "$HOME/.config/claudex/proxy-url"
```

Provision `proxy.key` directly from the protected source or a hidden local prompt, then apply mode `0600`; do not place the key in chat, command-line arguments, or shell history. The direct launcher reads these two files at startup and rejects an empty or multiline key. For a non-loopback HTTP endpoint, apply the explicit security decision required by the mode reference.

Before patching the shell, inspect the selected proxy's live model catalog. This profile uses `[1m]` suffixes on standard Astra and canonical Sol plus `1000000` for Claude Code's client-side managed window. Terra and Luna stay unsuffixed. When the catalog advertises a smaller maximum for a selected model, surface that mismatch and do not claim the settings raise the upstream limit. The variables remain inside both scoped launchers so ordinary `claude` sessions are unchanged.

Patch one clearly labeled block in the active shell startup file. Remove an older copy before adding a replacement so repeated runs stay idempotent. Preserve every unrelated alias and environment variable. For zsh, use:

```zsh
# Claude Code /model mapping for the selected Codex bridge.
unalias claudex claudex-direct 2>/dev/null
alias claudex-direct="$HOME/.local/bin/claudex-direct"
alias claudex='claudex-remote-control "Claudex Remote Control"'
```

The default `claudex` alias supplies a fixed Remote Control name before forwarding user arguments, so a positional Claude prompt is not mistaken for the session name expected by the launcher. The `claudex-direct` launcher retains the custom-base-url path for non-interactive automation and troubleshooting. Both executable launchers select Fable/standard Astra, map Opus directly to canonical Sol, default to `xhigh`, and compact at 600K. They append user arguments after these defaults so later options can override launch defaults.

Do not hard-code `CLAUDE_CODE_EFFORT_LEVEL`: it can override session choices and prevent ultracode workflows. Report an inherited global value, then rely on the scoped launchers to remove it so their explicit CLI defaults and overrides remain authoritative. CC should send `thinking.type: adaptive` and `output_config.effort`; do not substitute a fixed `MAX_THINKING_TOKENS` budget for this five-level contract.

Use `claudex --effort ultracode` or interactive `/effort ultracode` to keep CC's native `xhigh` plus workflow mode (requires CC 2.1.203+ and enabled dynamic workflows). Do not force-enable workflows against user settings. Confirm the actual request has the ultracode activation reminder and Workflow tool; a successful `xhigh` response alone proves neither workflow activation nor delegation. The bridge invokes model APIs, not a Codex agent. See [CC effort documentation](https://code.claude.com/docs/en/model-config#adjust-effort-level).

## 7. Verify end to end

Verify in increasing order of cost:

1. In `proxy-only` or `all`, confirm the local listener matches the authorized exposure: loopback by default, or the user's exact approved interface, TLS termination, and firewall scope. Verify correct-key success and wrong-key/missing-key rejection.
2. Query the selected proxy's `GET /v1/models` without printing the key and confirm these client-visible IDs are present:
   - `gpt-6-astra`
   - `gpt-6-astra-fast`
   - `gpt-5.6-sol`
   - `gpt-5.6-terra`
   - `gpt-5.6-luna`
3. In `proxy-only`, send minimal Responses API requests to canonical Astra, Sol, Terra, and Luna. Check exact output, resolved canonical model, returned effort, and reported service tier. Confirm the configured payload rule matches all three GPT-5.6 models. Stop after the proxy checks; no local Claude launcher is expected.
4. In `client-only` or `all`, validate `zsh -n ~/.zshrc`, launcher syntax, profile file permissions, and only non-secret launcher fields. Confirm `claudex` invokes `claudex-remote-control`, `claudex-direct` retains the selected custom-base-url path, Fable is standard Astra, Opus uses `gpt-5.6-sol[1m]`, and both launchers select `--model fable --effort xhigh --autocompact 600k`.
5. In `client-only` or `all`, send a minimal request through `claudex-direct` with no model override and require `gpt-6-astra[1m]`. Repeat with `--model opus`, `sonnet`, and `haiku`, and require canonical Sol, Terra, and Luna respectively. The direct fallback depends on the selected proxy's server-side GPT-5.6 rule. Inspect the returned service tier separately and describe Priority as unconfirmed unless upstream metadata reports it.
6. In `client-only` or `all`, start `claudex`, confirm the Remote Control banner appears, and verify Fable, Opus, Sonnet, and Haiku route as intended. Capture a redacted routectl test and require the Sol, Terra, and Luna forwarded bodies to contain `service_tier: priority` and `speed: fast`. Complete the official phone/web E2E gate before reporting Remote Control as fully verified.

For the default/Opus model, Read tool round-trip, and 1M client-accounting checks, run the included standard-library verifier:

```bash
python3 scripts/verify_profile.py
```

Run these from this skill directory in `client-only` or `all`. Repeat the profile verifier with `--effort max` and `--effort ultracode` as appropriate. It invokes `~/.local/bin/claudex-direct` by default; pass `--claudex` when the install uses a different layout. The verifiers do not establish upstream Priority or context capacity. Read [references/verification.md](references/verification.md) for the client-wire and real-upstream tests; do not confuse either stage alone with full E2E verification.

Example minimal checks after loading the shell config:

```zsh
source ~/.zshrc
claudex-direct -p --output-format json 'Reply with exactly ASTRA_STANDARD_OK'
claudex-direct -p --model opus --output-format json \
  'Reply with exactly SOL_PRIORITY_OK'
```

Verify Claude Code's effective accounting with a small JSON request:

```zsh
claudex-direct -p --tools "" --no-session-persistence \
  --output-format json 'Reply with exactly CONTEXT_OK' |
  jq '{result, models: (.modelUsage | to_entries | map({model: .key, contextWindow: .value.contextWindow}))}'
```

Require the reported model name to retain `[1m]` and `contextWindow: 1000000` before reporting success. The settings change Claude Code's model profile, management, and auto-compaction ceiling for this invocation; they do not prove that 1M tokens of user files fit in one request or raise a smaller upstream limit. Keep verification prompts small unless the user explicitly requests a costly near-limit test.

## 8. Configure the default official Remote Control entrypoint (`client-only` and `all`)

Skip this section in `proxy-only`. Do not add Remote Control to the custom-base-url `claudex-direct` alias: Claude Code rejects that combination. The default `claudex` alias must instead invoke the routectl launcher, which uses a process-scoped HTTPS proxy. It re-injects only Anthropic inference paths into a loopback router backed by the selected local or external CLIProxyAPI endpoint, while Anthropic control-plane traffic remains first-party.

Read [references/remote-control.md](references/remote-control.md) completely before installing routectl or generating its CA. Pin and review the documented source commit. Keep routectl HTTP on `127.0.0.1:8787` and routectl MITM on `127.0.0.1:8443`; in `all`, keep CLIProxyAPI on `127.0.0.1:8317`. Leave routectl listener auth off for this single-user loopback path. Set its provider URL to the value in `~/.config/claudex/proxy-url` and its `api_key_ref` to the absolute `file://` URL for `~/.config/claudex/proxy.key`; never embed the key in TOML, the launcher, logs, or chat.

Launch with the included script after routectl is healthy:

```bash
claudex
```

The launcher must unset `ANTHROPIC_BASE_URL`, Anthropic key/token variables, provider flags, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, and fixed effort overrides. It reads the proxy and CA from `routectl rc env` without `eval`, refuses a non-loopback proxy, scopes all variables to the Claude process, and launches with `--model fable --effort xhigh --autocompact 600k`, the standard Astra/GPT-5.6 mappings, and the 1M managed-context profile.

For reliable phone-side selection, start one named Fable/Astra session and one named Opus/Sol session:

```bash
scripts/claudex-remote-control "My workstation · Astra"
scripts/claudex-remote-control "My workstation · Sol" --model opus
```

Additional Claude arguments follow the launcher's defaults, so the later `--model opus` selects the canonical Sol mapping. In the official mobile app, the sessions can still appear as Fable and Opus because those are first-party UI labels. Require the local terminal identity and routectl evidence to show `gpt-6-astra[1m]` for Fable or `gpt-5.6-sol[1m]` for Opus. Do not use a Sonnet or Haiku picker entry as a substitute.

Do not depend on changing a mapped custom model inside an existing phone-controlled session. With prior assistant output, Claude Code asks for local confirmation before `/model` re-reads the full history, and mobile picker changes can be client-scoped or fail to match a custom model ID. Select the separately named session instead. State the tradeoff clearly: the Astra and Sol sessions do not share conversation context.

Do not declare success from an active `/remote-control` banner alone. Send a random exact-response prompt from the official phone or web client, observe the same message and response in the local session, require a new CLIProxyAPI `/v1/messages` request, and confirm routectl selected standard Astra. Repeat official-base-url requests through the same proxy for Opus/Sol, Sonnet/Terra, and Haiku/Luna. Require `contextWindow: 1000000` for Sol, capture the three outgoing tier fields, and record the response service tier rather than inferring a Priority grant from successful routing.

## 9. Modify mappings safely

- In `client-only`, do not mutate the external proxy unless the user separately authorized and provided access to administer it. Client model labels can change locally, and routectl can inject Priority/Fast on the default Remote Control path, but canonical target IDs and the proxy-wide GPT-5.6 Priority rules must already exist upstream for `claudex-direct`.
- To change Claude Code's Fable, Opus, Sonnet, Haiku, or Subagent selection, patch only the corresponding environment variable and the trailing default `--model` when requested. This profile uses Fable/standard Astra by default and requests Priority for Opus/Sol, Sonnet/Terra, and Haiku/Luna. Sol uses `[1m]`; keep Terra and Luna unsuffixed unless their upstream context support is separately verified. All routes keep CC-selected effort (launch default `xhigh`).
- To expose another client-visible alias, add it under `oauth-model-alias.codex`, keep the canonical upstream name in `name`, and decide explicitly whether `fork` should preserve the original.
- To attach request behavior to an alias, add a narrowly matched `payload` rule with `protocol: "codex"`.
- Restart or reload the proxy, refresh the shell, and repeat the model-list plus minimal-request checks after every mapping change.

## Troubleshooting

- **Expired device code:** rerun `--codex-device-login` and use the new code.
- **401 from the selected endpoint:** make `~/.config/claudex/proxy.key` match one key accepted by that proxy. In `client-only`, do not change the external service without separate authorization.
- **Unknown model:** inspect `/v1/models`, confirm the OAuth account exposes the unsuffixed canonical model, and verify the alias is under the `codex` channel. Keep `[1m]` out of the CLIProxyAPI OAuth alias configuration and off Terra/Luna mappings.
- **Astra Fast alias replaces canonical Astra:** set `fork: true` on the Astra Fast alias, then restart or reload the proxy.
- **Sol stays at xhigh after CC changes effort:** remove the legacy `"reasoning.effort": "xhigh"` payload override while preserving the Priority rule. Inspect `CLAUDE_CODE_EFFORT_LEVEL` precedence and capture CC's `thinking.type` and `output_config.effort`. Verify upstream metadata rather than inferring effort from the model's answer.
- **Ultracode only behaves like xhigh:** check the CC version, workflow setting, model capability detection, environment effort override, and activation reminder. Report disabled workflows honestly; do not rewrite the upstream effort to `ultra` as a workaround.
- **A GPT-5.6 route succeeds but reports the standard tier:** the route worked and the local payload override may have been sent, but Fast is not verified on that deployed path. Check whether CLIProxyAPI forwarded the HTTP/SSE request over its upstream WebSocket executor; do not use successful output, catalog capability, or latency as a substitute for tier evidence.
- **Claude Code shows stale mappings:** open a new shell or source the startup file, then restart Claude Code. If Claude Code starts from a GUI or a different shell, configure that launch environment because it may not read `.zshrc`.
- **Claude Code still reports less than 1M:** confirm both the `[1m]` suffix and `1000000` environment variable are present in the selected `claudex` or `claudex-direct` launcher, start a fresh shell, and repeat the JSON `modelUsage` check through `claudex-direct`.
- **Remote Control says custom base URL is unsupported:** confirm `claudex` resolves to `claudex-remote-control`, not `claudex-direct`. Do not spoof first-party mode or add more auth variables. Verify the routectl service and CA, then relaunch `claudex`; see [references/remote-control.md](references/remote-control.md).
- **Remote Control starts but inference reaches Anthropic:** verify the Claude child has no custom base/auth variables, the process has routectl's `HTTPS_PROXY` and CA, and the routectl provider targets the same selected proxy as `claudex-direct`. Require a proxy request-count increase and routectl model evidence.
- **The phone shows Fable or Opus instead of Astra or Sol:** this is expected first-party UI labeling, not proof of the upstream route. Verify the named session, terminal model header, and routectl/CLIProxy request evidence.
- **The phone model picker changes its checkmark but not the route:** stop using that picker for custom IDs. Launch or select the separately named Astra or Sol session; use the local terminal when preserving and switching an existing conversation is mandatory.
- **Service repeatedly restarts:** inspect `journalctl --user -u cliproxyapi.service`, validate YAML, verify binary permissions, and confirm the auth directory is writable under the service sandbox.
- **OAuth model list changes:** treat the latest catalog as authoritative and update mappings only to IDs the account currently exposes.

## Handoff

Report the selected mode, installed components, active paths, service state for components this machine owns, redacted proxy origin, exposed model IDs, shell mapping when present, and minimal request results. State whether the three canonical GPT-5.6 routes worked, whether the proxy-wide Priority rules and routectl payload overrides were installed, and whether Priority processing was actually confirmed. List any mode-specific gate that could not be run. Never include credentials or OAuth file contents.
