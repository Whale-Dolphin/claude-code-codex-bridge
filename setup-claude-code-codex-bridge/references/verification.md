# Effort verification

Run commands from the skill directory. Scripts use Python 3.9+ and the standard library; no global dependencies are required. Pass `--claudex` when the executable wrapper is not at `~/cliproxyapi/claudex`.

## Stage matrix

| Stage | Contract | Fixture | Assertion | Command | Frequency | Status |
| --- | --- | --- | --- | --- | --- | --- |
| CC client | Default and five efforts preserve model/level | Loopback SSE responder with dummy auth | Fable/Astra and Opus/Sol, adaptive thinking, exact effort; default xhigh | `python3 scripts/verify_effort.py client` | CC/wrapper changes | Implemented; run on target host |
| CC ultracode | CC owns workflow activation | Same responder; real installed CC | xhigh plus activation reminder and Workflow tool; absent reminder on ordinary efforts | Same client command | CC/wrapper changes | Implemented; does not execute a workflow |
| Real upstream | Five efforts survive bridge/upstream | Ten short Responses requests | Canonical model, matching returned effort, exact response | `python3 scripts/verify_effort.py upstream --key-file /protected/proxy-key` | Bridge/config changes | Implemented; consumes account usage |
| Full E2E | Actual wrapper, proxy, OAuth, model, and Read tool work together | Random temporary file | Exact file contents, tool round trip, resolved model, managed context 1000000 | `python3 scripts/verify_profile.py`; repeat with `--effort max` and `--effort ultracode` | Deployment | Implemented; consumes account usage |
| Access boundary | Existing endpoint/key remain unchanged | Authorized host, correct/incorrect/no key | Correct key succeeds; wrong/missing key rejected | Existing deployment HTTP auth checks | Deployment | Host-specific check |

The client stage launches the real wrapper but overrides only the test session's API URL/auth with a loopback fake responder. It neither calls the upstream nor changes the wrapper/settings. It prints selected fields only, never headers or prompts. The ultracode check looks for CC's activation reminder; if a future version changes that contract, inspect the request safely before updating the assertion.

The upstream stage calls the deployed bridge's Responses endpoint directly. It checks returned `reasoning.effort` and canonical model, not the model's self-description. An upstream response with `service_tier: default` means Priority was not confirmed, even though the Fast alias requests it. This stage alone does not prove CC emitted the right effort or that the Anthropic translation path works; run the client and full E2E stages too.

The full E2E entrypoint is the actual installed `claudex` executable. No core component is mocked. The fixture is a random file in an isolated temporary directory; only Read is permitted and external MCP configuration is disabled. It is a small tool-use regression, not a statistical quality evaluation, a near-limit context test, or proof that ultracode actually delegated agents. Verify a bounded real Workflow separately when delegation itself is in scope.

## Pass credentials without exposing them

Prefer an existing protected key-only file. If the key is only in YAML on macOS, use the installed Ruby parser and a pipe:

```bash
ruby -r yaml -e 'print YAML.load_file(ARGV[0])["api-keys"].first' \
  "$HOME/cliproxyapi/config.yaml" |
  python3 scripts/verify_effort.py upstream --key-stdin
```

Do not enable shell tracing. Never pass keys as command-line values or print live YAML. For an explicitly authorized public endpoint, provide its `--base-url` and retain the user's existing exposure policy; do not introduce a tunnel and call it a public-IP test.
