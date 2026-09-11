# Installation modes

Choose the installation mode before changing files or services. A mode is a component boundary, not a model-mapping choice: every client installation uses the same Fable/Astra, GPT-5.6 Priority, effort, context, and Remote Control profile.

## Mode matrix

| Mode | Install on this machine | Proxy used by `claudex` | Required input |
| --- | --- | --- | --- |
| `proxy-only` | CLIProxyAPI, Codex OAuth, proxy service | None; no Claude launcher is installed | Whether another machine must reach it; exact authorized bind/TLS/firewall scope if yes |
| `client-only` | Claude Code launchers, client profile, routectl | Existing external CLIProxyAPI-compatible endpoint | Base URL and proxy key |
| `all` | Both proxy and client components | New or existing local CLIProxyAPI | No second key; reuse the generated or existing local proxy key |

Ask the user to select one of these three names. If the user already selected one, do not ask again. Do not infer `all` merely because remnants of both components exist on disk.

## Shared client profile

`client-only` and `all` use the same files:

```text
~/.config/claudex/proxy-url   one CLIProxyAPI base URL, without /v1
~/.config/claudex/proxy.key   one proxy key, mode 0600
~/.local/bin/claudex-direct
~/.local/bin/claudex-remote-control
```

The direct launcher reads those files at startup. routectl's `providers.cliproxy.base_url` must contain the same URL, and `api_key_ref` must point to the same `proxy.key` file. This keeps direct and official Remote Control paths on one selected proxy.

Use the endpoint origin, for example `http://127.0.0.1:8317` or `https://bridge.example.com`. Remove one trailing slash. Do not store `/v1`, credentials, a query, or a fragment in `proxy-url`.

Create the profile directory and install the launchers with private defaults:

```bash
install -d -m 0700 "$HOME/.config/claudex" "$HOME/.local/bin"
install -m 0755 scripts/claudex-direct "$HOME/.local/bin/claudex-direct"
install -m 0755 scripts/claudex-remote-control "$HOME/.local/bin/claudex-remote-control"
```

Write the URL without exposing a secret:

```bash
printf '%s\n' '<proxy-base-url>' > "$HOME/.config/claudex/proxy-url"
chmod 0600 "$HOME/.config/claudex/proxy-url"
```

For the key, ask the user for either an existing protected key-only file or permission to enter it through a hidden local terminal prompt. Do not ask the user to paste the key into chat, place it in command-line arguments, or put it in shell history. Copy or write it directly to `proxy.key`, apply mode `0600`, then unset any temporary shell variable. Do not print it during verification.

Patch one labeled shell block without embedding the URL or key:

```zsh
# Claude Code /model mapping for the selected Codex bridge.
unalias claudex claudex-direct 2>/dev/null
alias claudex-direct="$HOME/.local/bin/claudex-direct"
alias claudex='claudex-remote-control "Claudex Remote Control"'
```

## `proxy-only`

Run only the local proxy sections of the main skill:

1. Install or upgrade CLIProxyAPI.
2. Configure the optional Astra Fast alias and the canonical Sol, Terra, and Luna Priority override.
3. Complete Codex OAuth device login.
4. Start the proxy as a user service.
5. Verify listener scope, key enforcement, model catalog, and minimal Astra/Sol/Terra/Luna requests.

Skip Claude Code installation, the `~/.config/claudex` profile, both launchers, routectl, and shell aliases.

Keep the proxy on loopback when it is for the same machine. If it must serve another machine, stop before changing the bind address. Ask for the exact client network, bind interface, TLS termination, and firewall scope; expose only what the user authorizes. A proxy key alone does not protect prompts or bearer credentials from interception over plaintext HTTP.

At handoff, report the endpoint as a redacted origin and identify the protected local configuration that contains its accepted keys. If another client needs the key, use a secure transfer path outside chat. Never return the key itself.

## `client-only`

Do not install, configure, authorize, restart, or otherwise mutate CLIProxyAPI on this machine.

Before writing the client profile, collect:

1. The external CLIProxyAPI-compatible base URL, without `/v1`.
2. The proxy key through a protected key file or hidden local entry.

Require HTTPS when the endpoint crosses an untrusted network. If the user supplies plaintext HTTP for a non-loopback endpoint, explain that prompts and the bearer key can be read in transit, then require explicit acceptance of that exact endpoint before continuing.

Confirm the external endpoint provides the contracts this profile needs:

- Anthropic-compatible `/v1/messages`, `/v1/messages/count_tokens`, and `/v1/models` for Claude Code.
- `gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` under the expected names.
- Server-side rules that apply `service_tier: priority` to every canonical `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` request. The local routectl profile also adds `service_tier: priority` and `speed: fast` to these models on the default `claudex` path, but the client cannot create server-side rules on an external proxy for the independent `claudex-direct` fallback.
- A real streaming or non-streaming response whose completed metadata reports `service_tier: priority`. A catalog `service_tiers` field is only a capability declaration and does not prove the HTTP/SSE transport actually received Priority processing.
- Responses API support when running the optional real-upstream effort verifier.

Install the shared client profile and both launchers. Configure local routectl with the external URL and `file://` reference to the local protected `proxy.key`; routectl itself remains loopback-only. Add model-scoped `payload_extras` for canonical Sol, Terra, and Luna so the default Remote Control path always sends `service_tier: priority` and `speed: fast`. Verify all four model paths through `claudex-direct`, inspect the reported service tier separately, then verify the official Remote Control path and its local payload overrides.

## `all`

Run the proxy installation first. Create the shared client profile with:

```text
proxy-url = http://127.0.0.1:8317
proxy.key = the same local key accepted by CLIProxyAPI
```

Do not generate a second client key. If an existing proxy installation has multiple accepted keys, preserve them and select one existing key for the client profile without printing it. Then install the client launchers, routectl, and shell aliases and run both proxy and client verification gates.

## Switching the selected proxy later

Changing from a local to an external proxy is a client-profile update. Back up `proxy-url`, `proxy.key`, and routectl's config; replace the URL and key files; update routectl's provider URL; validate both configs; restart routectl; then rerun direct and Remote Control checks. Do not uninstall or stop a local proxy unless the user separately asks for that lifecycle change.

Changing from an external to a local proxy requires the local proxy to pass its own service and OAuth checks before changing the client profile. Keep the previous protected profile files as rollback material until the new end-to-end checks pass.
