#!/usr/bin/env python3
"""Verify the installed claudex default and Opus mappings using real Read calls."""

import argparse
import json
import secrets
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--claudex',
        type=Path,
        default=Path.home() / '.local/bin/claudex-direct',
    )
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--effort', choices=('low', 'medium', 'high', 'xhigh', 'max', 'ultracode'))
    args = parser.parse_args()
    wrapper = args.claudex.expanduser().resolve(strict=True)
    effort_args = ['--effort', args.effort] if args.effort else []
    routes = [
        ('fable-default', [], 'gpt-6-astra[1m]'),
        ('opus', ['--model', 'opus'], 'gpt-5.6-sol-fast[1m]'),
    ]
    with tempfile.TemporaryDirectory(prefix='claudex-profile-') as workdir:
        expected = 'PROFILE_OK_' + secrets.token_hex(8)
        (Path(workdir) / 'fixture.txt').write_text(expected + '\n', encoding='utf-8')
        for label, model_args, expected_model in routes:
            result = subprocess.run([
                str(wrapper), '-p', *model_args, *effort_args,
                '--tools', 'Read', '--allowedTools', 'Read',
                '--setting-sources', '', '--strict-mcp-config',
                '--mcp-config', '{"mcpServers":{}}',
                '--no-session-persistence', '--output-format', 'json',
                'Read fixture.txt using the Read tool. Reply with exactly its contents.',
            ], cwd=workdir, capture_output=True, text=True, timeout=args.timeout)
            if result.returncode:
                raise SystemExit(f'{label}: claudex exited with status {result.returncode}')
            payload = json.loads(result.stdout)
            model_usage = payload.get('modelUsage', {}).get(expected_model, {})
            passed = (
                payload.get('is_error') is False
                and payload.get('result', '').strip() == expected
                and payload.get('num_turns', 0) >= 2
                and not payload.get('permission_denials')
                and model_usage.get('contextWindow') == 1000000
            )
            print(json.dumps({
                'route': label, 'passed': passed, 'selected_effort': args.effort or 'default',
                'expected_model': expected_model,
                'reported_models': list(payload.get('modelUsage', {})),
                'contextWindow': model_usage.get('contextWindow'),
                'tool_round_trip': payload.get('num_turns', 0) >= 2,
                'client_service_tier': payload.get('usage', {}).get('service_tier'),
            }), flush=True)
            if not passed:
                raise SystemExit(f'{label}: model, tool, or managed-context validation failed')


if __name__ == '__main__':
    main()
