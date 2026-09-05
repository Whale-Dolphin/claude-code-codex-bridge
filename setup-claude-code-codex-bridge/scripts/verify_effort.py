#!/usr/bin/env python3
"""Check CC wire parameters separately from real upstream reasoning metadata."""

import argparse
import json
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROUTES = {'fable': 'gpt-6-astra-fast', 'opus': 'gpt-5.6-sol-fast'}
LEVELS = ('low', 'medium', 'high', 'xhigh', 'max')


def verify_client(wrapper: Path, timeout: int) -> None:
    records: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: object) -> None:
            # Never log headers, prompts, or credentials.
            pass

        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if self.path.split('?')[0] != '/v1/messages':
                data = b'{"input_tokens":1}'
                content_type = 'application/json'
            else:
                records.append({
                    'model': body.get('model'),
                    'thinking_type': body.get('thinking', {}).get('type'),
                    'effort': body.get('output_config', {}).get('effort'),
                    'workflow_tool': any(t.get('name') == 'Workflow'
                                         for t in body.get('tools', [])),
                    'ultracode_active': 'Ultracode is on' in json.dumps(
                        body.get('messages', [])),
                })
                message = {
                    'id': 'msg_effort_test', 'type': 'message', 'role': 'assistant',
                    'model': body['model'], 'content': [], 'stop_reason': None,
                    'stop_sequence': None, 'usage': {'input_tokens': 1, 'output_tokens': 1},
                }
                events = [
                    ('message_start', {'type': 'message_start', 'message': message}),
                    ('content_block_start', {'type': 'content_block_start', 'index': 0,
                                            'content_block': {'type': 'text', 'text': ''}}),
                    ('content_block_delta', {'type': 'content_block_delta', 'index': 0,
                                            'delta': {'type': 'text_delta', 'text': 'EFFORT_OK'}}),
                    ('content_block_stop', {'type': 'content_block_stop', 'index': 0}),
                    ('message_delta', {'type': 'message_delta',
                                       'delta': {'stop_reason': 'end_turn', 'stop_sequence': None},
                                       'usage': {'output_tokens': 1}}),
                    ('message_stop', {'type': 'message_stop'}),
                ]
                data = ''.join(f'event: {name}\ndata: {json.dumps(value)}\n\n'
                               for name, value in events).encode()
                content_type = 'text/event-stream'
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            settings = {'env': {
                'ANTHROPIC_BASE_URL': f'http://127.0.0.1:{server.server_port}',
                'ANTHROPIC_AUTH_TOKEN': 'effort-test-placeholder',
                'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
            }}
            for label, model in ROUTES.items():
                for effort in ('default', *LEVELS, 'ultracode'):
                    records.clear()
                    model_args = [] if label == 'fable' else ['--model', label]
                    effort_args = [] if effort == 'default' else ['--effort', effort]
                    with tempfile.TemporaryDirectory(prefix='claudex-effort-') as cwd:
                        result = subprocess.run([
                            str(wrapper), '-p', *model_args, *effort_args,
                            '--settings', json.dumps(settings), '--setting-sources', '',
                            '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                            '--no-session-persistence', '--output-format', 'json',
                            'Reply exactly EFFORT_OK',
                        ], cwd=cwd, capture_output=True, text=True, timeout=timeout)
                    if result.returncode:
                        raise SystemExit(f'{label}/{effort}: CC exited {result.returncode}')
                    response = json.loads(result.stdout)
                    expected = 'xhigh' if effort in ('default', 'ultracode') else effort
                    passed = (
                        not response.get('is_error') and response.get('result') == 'EFFORT_OK'
                        and bool(records)
                        and all(r['model'] == model and r['effort'] == expected
                                and r['thinking_type'] == 'adaptive'
                                and r['ultracode_active'] == (effort == 'ultracode')
                                and (effort != 'ultracode' or r['workflow_tool'])
                                for r in records)
                    )
                    print(json.dumps({'stage': 'client', 'route': label,
                                      'selected_effort': effort, 'passed': passed,
                                      'requests': records}), flush=True)
                    if not passed:
                        raise SystemExit(f'{label}/{effort}: CC wire contract failed')
        finally:
            server.shutdown()
            thread.join()


def verify_upstream(base_url: str, key: str, timeout: int) -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for label, model in ROUTES.items():
        for effort in LEVELS:
            body = {
                'model': model, 'input': 'Reply exactly EFFORT_OK',
                'reasoning': {'effort': effort}, 'service_tier': 'default',
                'store': False, 'max_output_tokens': 256,
            }
            request = urllib.request.Request(
                base_url.rstrip('/') + '/v1/responses', data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            try:
                with opener.open(request, timeout=timeout) as response:
                    payload = json.load(response)
            except urllib.error.HTTPError as exc:
                raise SystemExit(f'{label}/{effort}: upstream HTTP {exc.code}') from None
            output = ''.join(c.get('text', '') for item in payload.get('output', [])
                             for c in item.get('content', [])
                             if c.get('type') == 'output_text').strip()
            actual_effort = payload.get('reasoning', {}).get('effort')
            passed = (payload.get('model') == model.removesuffix('-fast')
                      and actual_effort == effort and output == 'EFFORT_OK')
            print(json.dumps({'stage': 'upstream', 'route': label, 'passed': passed,
                              'requested_effort': effort, 'upstream_effort': actual_effort,
                              'upstream_model': payload.get('model'),
                              'upstream_service_tier': payload.get('service_tier')}), flush=True)
            if not passed:
                raise SystemExit(f'{label}/{effort}: upstream effort or model mismatch')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('client', 'upstream'))
    parser.add_argument('--claudex', type=Path, default=Path.home() / 'cliproxyapi/claudex')
    parser.add_argument('--base-url', default='http://127.0.0.1:8317')
    keys = parser.add_mutually_exclusive_group()
    keys.add_argument('--key-file', type=Path)
    keys.add_argument('--key-stdin', action='store_true')
    parser.add_argument('--timeout', type=int, default=120)
    args = parser.parse_args()
    if args.stage == 'client':
        verify_client(args.claudex.expanduser().resolve(strict=True), args.timeout)
    else:
        if not args.key_file and not args.key_stdin:
            parser.error('upstream requires --key-file or --key-stdin; never put keys in argv')
        key = (args.key_file.expanduser().read_text() if args.key_file else sys.stdin.read()).strip()
        if not key:
            parser.error('empty proxy key')
        verify_upstream(args.base_url, key, args.timeout)


if __name__ == '__main__':
    main()
