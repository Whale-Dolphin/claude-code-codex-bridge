# Effort verification

Run commands from the skill directory. Scripts use Python 3.9+ and the standard library; no global dependencies are required. Client checks expect `~/.local/bin/claudex-direct` by default. Pass `--claudex` when the executable wrapper uses another path.

## Stage matrix

| Stage | Contract | Fixture | Assertion | Command | Frequency | Status |
| --- | --- | --- | --- | --- | --- | --- |
| CC client | Default and five efforts preserve model/level | Loopback SSE responder with dummy auth | Fable/Astra and Opus/Sol, adaptive thinking, exact effort; default xhigh | `python3 scripts/verify_effort.py client` | CC/wrapper changes | Implemented; run on target host |
| CC native Fast | Fast state changes wire intent without changing the Sol route | Loopback SSE responder with dummy auth | Fast off omits `speed` and beta; Fast on sends `speed: "fast"` and `fast-mode-2026-02-01` | `python3 scripts/verify_fast.py` | CC/model-mapping changes | Implemented; passed on Claude Code 2.1.268 |
| CC ultracode | CC owns workflow activation | Same responder; real installed CC | xhigh plus activation reminder and Workflow tool; absent reminder on ordinary efforts | Same client command | CC/wrapper changes | Implemented; does not execute a workflow |
| Real upstream | Five efforts survive bridge/upstream | Ten short Responses requests | Canonical model, matching returned effort, exact response | `python3 scripts/verify_effort.py upstream` for a client profile, or add `--base-url` and `--key-file` | Bridge/config changes | Implemented; consumes account usage |
| Full E2E | Actual wrapper, proxy, OAuth, model, and Read tool work together | Random temporary file | Exact file contents, tool round trip, resolved model, managed context 1000000 | `python3 scripts/verify_profile.py`; repeat with `--effort max` and `--effort ultracode` | Deployment | Implemented; consumes account usage |
| Access boundary | Existing endpoint/key remain unchanged | Authorized host, correct/incorrect/no key | Correct key succeeds; wrong/missing key rejected | Existing deployment HTTP auth checks | Deployment | Host-specific check |
| Official RC split | Claude keeps first-party control plane while inference uses CLIProxyAPI | routectl selective MITM on loopback | Inference path re-injected; control path forwarded; other hosts blind-tunneled | See `references/remote-control.md` | Claude/routectl changes | Ubuntu E2E validated at pinned versions |
| Official mobile E2E | Phone controls the local Claude session and its inference uses Astra | Random exact-response phone prompt | Prompt/response visible locally, bridge request count increases, routectl selects standard Astra | `claudex`, then official phone/web client | Claude/routectl changes | Required after deploying this default change; not automatable locally |

The client stage launches the real wrapper with a temporary `CLAUDEX_CONFIG_DIR` containing a loopback fake URL and dummy key. This verifies that the wrapper reads the split client profile and sends its key without touching the installed profile or calling the real upstream. It prints a boolean auth result and selected request fields, never headers, keys, or prompts. The ultracode check looks for CC's activation reminder; if a future version changes that contract, inspect the request safely before updating the assertion.

The upstream stage calls the selected bridge's Responses endpoint directly. With no overrides it reads `~/.config/claudex/proxy-url` and `proxy.key`. A `proxy-only` host without a client profile must pass `--base-url` plus `--key-file` or `--key-stdin`. It checks returned `reasoning.effort` and canonical model, not the model's self-description. An upstream response with `service_tier: default` means Priority was not confirmed, even when native Fast requested it. This stage alone does not prove CC emitted the right effort, native Fast fields, or that the Anthropic translation path works; run the client, Fast-wire, and full E2E stages too when a client is installed.

The automated full E2E entrypoint is the installed direct wrapper, which the shell also exposes as `claudex-direct`; `verify_profile.py` requires a non-interactive executable and cannot exercise Remote Control. No core inference component is mocked. The fixture is a random file in an isolated temporary directory; only Read is permitted and external MCP configuration is disabled. It is a small tool-use regression, not a statistical quality evaluation, a near-limit context test, or proof that ultracode actually delegated agents. Verify the default interactive `claudex` Remote Control path separately and verify a bounded real Workflow when delegation itself is in scope.

Official Remote Control is the default interactive `claudex` path, but it remains technically separate from the `claudex-direct` custom-base-url path because Claude Code rejects that URL in Remote Control. Its E2E gate must use the official phone or web client and evidence both control-plane connectivity and bridge-side inference. An active banner alone is insufficient. Read [remote-control.md](remote-control.md) for the pinned implementation, security boundary, commands, and observed model-name normalization.

## Pass credentials without exposing them

Prefer the protected `~/.config/claudex/proxy.key` file; the upstream verifier uses it automatically for `client-only` and `all`. For `proxy-only`, pass an existing protected key-only file. If the key is only in YAML on macOS, use the installed Ruby parser and a pipe:

```bash
ruby -r yaml -e 'print YAML.load_file(ARGV[0])["api-keys"].first' \
  "$HOME/cliproxyapi/config.yaml" |
  python3 scripts/verify_effort.py upstream --key-stdin
```

Do not enable shell tracing. Never pass keys as command-line values or print live YAML. For an explicit endpoint override, provide its `--base-url` and retain the user's existing exposure policy; do not introduce a tunnel and call it a public-IP test.
