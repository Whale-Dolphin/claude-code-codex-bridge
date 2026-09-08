# Official Remote Control with the Codex bridge

Claude Code disables official Remote Control when `ANTHROPIC_BASE_URL` points at a custom endpoint. The supported bridge profile therefore cannot launch Remote Control with the ordinary `claudex` alias.

The verified compatibility path uses routectl's loopback-only selective MITM proxy. Claude Code still sees `https://api.anthropic.com`: routectl re-injects only `/v1/messages`, `/v1/messages/count_tokens`, and `/v1/models` into its local router, then sends those requests to CLIProxyAPI. Anthropic control-plane requests remain first-party traffic and every other host uses an opaque CONNECT tunnel.

```text
Claude Code / official mobile app
              |
      HTTPS_PROXY 127.0.0.1:8443
              |
        routectl selective MITM
          /                 \
 inference paths        control-plane paths
        |                       |
 routectl 127.0.0.1:8787   api.anthropic.com
        |
 CLIProxyAPI 127.0.0.1:8317
        |
 Codex OAuth: Astra Fast / Sol Fast
```

This is a compatibility layer, not a way to make Claude Code accept a custom `ANTHROPIC_BASE_URL` directly.

## Validated versions

The real Ubuntu E2E on 2026-09-08 used:

- Ubuntu 24.04 x86_64
- Claude Code 2.1.224 with a Claude Max login for the full split-path E2E
- Claude Code 2.1.263 for the follow-up named Sol Remote Control session
- CLIProxyAPI 7.2.154
- routectl commit `39a445f42aa5dee310661299b3fb2a868c472354`

The Remote Control implementation is newer than routectl's v0.9.0 tag. Pin the full commit above until a tagged release containing it is reviewed. That source requires Rust 1.95. Build the reviewed checkout rather than piping a remote installer into a shell:

```bash
git clone https://github.com/meepolabs/routectl.git
cd routectl
git checkout --detach 39a445f42aa5dee310661299b3fb2a868c472354
cargo test --locked -p routectl-cli proxy:: -- --test-threads=1
cargo build --locked --release -p routectl-cli
install -m 0755 target/release/routectl "$HOME/.local/bin/routectl"
```

The validated proxy suite passed 78 tests. Re-run it on the target host and re-review the pin before updating it.

## Prerequisites

1. Finish the normal CLIProxyAPI setup and verify both Fast aliases locally.
2. Sign Claude Code into a subscription account with `claude auth login --claudeai`. `claude auth status --json` must report `loggedIn: true`, `authMethod: claude.ai`, and a subscription type that supports Remote Control.
3. Store the CLIProxyAPI local key in a separate mode-0600 file for routectl. Do not put the key in the routectl TOML or launcher.
4. Keep CLIProxyAPI, routectl's HTTP listener, and its MITM listener on loopback. Do not expose 8317, 8787, or 8443.

## routectl configuration

Replace the absolute paths and `tested_cc_version`. `api_key_ref` must point at the same random local key accepted by CLIProxyAPI. Intentionally omit `[server.auth]`: routectl's MITM re-injection carries Claude's OAuth header, so listener auth would reject it.

```toml
[server]
host = "127.0.0.1"
port = 8787
max_body_bytes = 67108864

[mitm]
upstream_origin = "https://api.anthropic.com"
listen_port = 8443
cert_dir = "/home/you/.config/routectl/mitm-certs"
mitm_host = "api.anthropic.com"
tested_cc_version = "2.1.224"
credential_source = "own"

[providers.cliproxy]
kind = "anthropic-api"
base_url = "http://127.0.0.1:8317"
api_key_ref = "file:///home/you/.config/routectl/cliproxy.key"
auth_kind = "api-key"

[models.astra-fast]
provider = "cliproxy"
upstream = "gpt-6-astra-fast"
reported_model = "gpt-6-astra-fast[1m]"
supports_adaptive_thinking = true
effort_levels = ["low", "medium", "high", "xhigh", "max"]
visible_routectl_provider = false

[models.sol-fast]
provider = "cliproxy"
upstream = "gpt-5.6-sol-fast"
reported_model = "gpt-5.6-sol-fast[1m]"
supports_adaptive_thinking = true
effort_levels = ["low", "medium", "high", "xhigh", "max"]
visible_routectl_provider = false

[aliases]
"gpt-6-astra-fast" = "astra-fast"
"gpt-6-astra-fast[1m]" = "astra-fast"
"gpt-5.6-sol-fast" = "sol-fast"
"gpt-5.6-sol-fast[1m]" = "sol-fast"
default = "astra-fast"
```

Validate and launch routectl with prompt/body logging disabled:

```bash
routectl --config "$HOME/.config/routectl/config.toml" config check
ROUTECTL_LOG_REDACT_PROMPTS=1 ROUTECTL_TRACE_BODY_BYTES=0 \
  routectl --config "$HOME/.config/routectl/config.toml" serve
```

For a persistent user service, carry both environment variables into the unit. The routectl config, CA directory, usage database, and key file must remain readable/writable only as required by that user service.

## Launch official Remote Control

Install the included launcher somewhere on `PATH`, or invoke it directly:

```bash
ROUTECTL_CONFIG="$HOME/.config/routectl/config.toml" \
  scripts/claudex-remote-control "My workstation"
```

The launcher parses `routectl rc env` without `eval`, refuses a non-loopback proxy, and verifies the generated CA. It explicitly removes custom base URL, API key, provider, global proxy, disabled-traffic, and fixed-effort variables before starting Claude Code. It then scopes routectl's `HTTPS_PROXY`, CA, Fast mappings, and 1M managed-context setting to that one process.

The first argument is the Remote Control session name. Additional Claude options are appended after the default `--model fable --effort xhigh`, so an explicit later option can override a launch default when the installed Claude Code supports it.

### Mobile model labels and reliable switching

The official Claude mobile app and `claude.ai/code` own the Remote Control UI. They continue to display their built-in model families instead of routectl's custom Codex model IDs. This is expected: the control plane stays first-party, while the process-scoped proxy changes only the selected inference paths.

| Official client label | Launcher selection | Verified bridge route |
| --- | --- | --- |
| Fable, currently shown as `Fable 5.1` | default `--model fable` | `gpt-6-astra-fast[1m]` |
| Opus, currently shown as `Opus 5` | later `--model opus` | `gpt-5.6-sol-fast[1m]` |

The displayed version text is controlled by Anthropic and can change independently of this repository. Do not use it as route evidence. The phone may also display its own effort wording; require the terminal and captured request to establish the effective model and effort.

Use two named Remote Control sessions when the operator needs to choose Astra or Sol entirely from the phone:

```bash
scripts/claudex-remote-control "My workstation · Astra"
scripts/claudex-remote-control "My workstation · Sol" --model opus
```

Select the desired name from the mobile Code session list. This is the reliable boundary because the launch model is fixed before the session has history. It does not preserve one shared context across the two sessions.

Do not treat the in-session mobile picker as authoritative for custom model IDs. Reported Remote Control behavior includes a picker checkmark that does not change the terminal-side custom model and model changes that are applied only with a subsequent remote-originated message. Claude Code also asks for local confirmation when `/model` changes a conversation that already has assistant output, because the next model must re-read the full uncached history. When a same-context switch is required, perform and confirm it on the local terminal, then verify the next request's route.

References for these boundaries:

- [Claude Code model configuration](https://code.claude.com/docs/en/model-config)
- [Android Remote Control custom-model picker report](https://github.com/anthropics/claude-code/issues/65373)
- [Remote picker propagation report](https://github.com/anthropics/claude-code/issues/83472)

## Verification matrix

| Stage | Contract | Fixture | Assertion | Command | Frequency | Status |
| --- | --- | --- | --- | --- | --- | --- |
| routectl source | Selective MITM implementation is intact | Pinned source | Proxy, CA, split, control-plane, and log-redaction tests pass | `cargo test --locked -p routectl-cli proxy:: -- --test-threads=1` | Pin update | 78 passed on validated Ubuntu |
| Local binds | No new public listener | Three processes | 8317, 8787, and 8443 bind only to loopback | `ss -lntp` | Deployment | Passed on validated Ubuntu |
| Access boundary | CLIProxy key still protects inference | Correct, wrong, missing key | 200, 401, 401 | `GET /v1/models` against 8317 | Deployment | Passed on validated Ubuntu |
| TLS split | Only inference is re-injected | Real CONNECT/TLS requests | `/v1/models` comes from routectl; `/api/hello` reaches Anthropic; other host is blind-tunneled | `curl --proxy ... --cacert ...` | Claude/routectl update | Passed on validated Ubuntu |
| Fable path | Official URL with no custom auth reaches Astra | Exact short prompt | Exact text, Astra Fast route, managed context 1000000 | `claude -p --model fable ...` with only process-scoped proxy/CA | Deployment | Passed on validated Ubuntu |
| Opus path | Official URL with no custom auth reaches Sol | Exact short prompt at `max` | Exact text, Sol Fast route, managed context 1000000 | `claude -p --model opus --effort max ...` | Deployment | Passed on validated Ubuntu |
| Mobile E2E | Official Remote Control operates the local session while inference uses the bridge | Message sent from official mobile client | Phone message and exact response appear locally; CLIProxy request count increases; routectl records Astra Fast | Launcher, then send a random exact-response prompt from phone | Claude/routectl update | Passed on validated Ubuntu |
| Named Sol session | Phone can select a Sol-specific session without an in-session model change | Launcher with `--model opus`, exact short prompt, mobile sync | Terminal reports Sol Fast, routectl records Sol Fast, exact response appears in the official client | Start the second named launcher session and inspect local route evidence | Claude/routectl update | Passed on Claude Code 2.1.263 |

Claude Code versions may normalize the `modelUsage` key differently. Accept either the Fast name with `[1m]` or without it only when the resolved route is correct and `contextWindow` is exactly `1000000`. This remains client-side managed context, not proof of 1M upstream capacity. Treat Priority as unconfirmed unless returned metadata reports it; the validated requests reported the standard tier.

## Security and rollback

routectl terminates TLS for `api.anthropic.com` locally, so the process can see Claude requests and the full-scope Claude session token. Use only the reviewed pinned source, keep every listener on loopback, set prompt/body logging controls, and scope the CA through the launcher instead of exporting it in the shell.

To disable the compatibility layer, exit the Remote Control process, stop routectl, and launch ordinary `claude` without the launcher. Removing `[mitm]` and restarting routectl removes the extra listener. The normal `claudex` custom-base-url profile remains independent.

Official references:

- [Claude Code Remote Control](https://code.claude.com/docs/en/remote-control)
- [routectl Remote Control design](https://github.com/meepolabs/routectl/blob/39a445f42aa5dee310661299b3fb2a868c472354/docs/REMOTE-CONTROL.md)
- [CLIProxyAPI releases](https://github.com/router-for-me/CLIProxyAPI/releases)
