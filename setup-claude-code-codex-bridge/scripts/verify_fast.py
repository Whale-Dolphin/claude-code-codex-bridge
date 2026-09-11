#!/usr/bin/env python3
"""Verify Claude Code's native Fast toggle on the Opus bridge route."""

import argparse
import json
import os
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


OPUS_CLIENT_MODEL = "claude-opus-5[1m]"
OPUS_WIRE_MODEL = "claude-opus-5"


def verify_client(claude: Path, timeout: int) -> None:
    records: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: object) -> None:
            # Never log headers, prompts, or credentials.
            pass

        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path.split("?")[0] != "/v1/messages":
                data = b'{"input_tokens":1}'
                content_type = "application/json"
            else:
                records.append(
                    {
                        "model": body.get("model"),
                        "speed": body.get("speed"),
                        "fast_beta": "fast-mode-2026-02-01"
                        in self.headers.get("anthropic-beta", ""),
                    }
                )
                message = {
                    "id": "msg_fast_test",
                    "type": "message",
                    "role": "assistant",
                    "model": body["model"],
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                }
                events = [
                    ("message_start", {"type": "message_start", "message": message}),
                    (
                        "content_block_start",
                        {
                            "type": "content_block_start",
                            "index": 0,
                            "content_block": {"type": "text", "text": ""},
                        },
                    ),
                    (
                        "content_block_delta",
                        {
                            "type": "content_block_delta",
                            "index": 0,
                            "delta": {"type": "text_delta", "text": "FAST_OK"},
                        },
                    ),
                    ("content_block_stop", {"type": "content_block_stop", "index": 0}),
                    (
                        "message_delta",
                        {
                            "type": "message_delta",
                            "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                            "usage": {"output_tokens": 1},
                        },
                    ),
                    ("message_stop", {"type": "message_stop"}),
                ]
                data = "".join(
                    f"event: {name}\ndata: {json.dumps(value)}\n\n"
                    for name, value in events
                ).encode()
                content_type = "text/event-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for fast_mode in (False, True):
                records.clear()
                env = os.environ.copy()
                env.update(
                    {
                        "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}",
                        "ANTHROPIC_AUTH_TOKEN": "fast-test-placeholder",
                        "ANTHROPIC_API_KEY": "",
                        "ANTHROPIC_DEFAULT_OPUS_MODEL": OPUS_CLIENT_MODEL,
                        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                        "CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK": "1",
                    }
                )
                settings = {"fastMode": fast_mode}
                with tempfile.TemporaryDirectory(prefix="claudex-fast-") as cwd:
                    result = subprocess.run(
                        [
                            str(claude),
                            "-p",
                            "--model",
                            "opus",
                            "--settings",
                            json.dumps(settings),
                            "--setting-sources",
                            "",
                            "--strict-mcp-config",
                            "--mcp-config",
                            '{"mcpServers":{}}',
                            "--no-session-persistence",
                            "--output-format",
                            "json",
                            "Reply exactly FAST_OK",
                        ],
                        cwd=cwd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        env=env,
                    )
                if result.returncode:
                    raise SystemExit(
                        f"fastMode={fast_mode}: CC exited {result.returncode}"
                    )
                response = json.loads(result.stdout)
                expected_speed = "fast" if fast_mode else None
                passed = (
                    not response.get("is_error")
                    and response.get("result") == "FAST_OK"
                    and bool(records)
                    and all(
                        record["model"] == OPUS_WIRE_MODEL
                        and record["speed"] == expected_speed
                        and record["fast_beta"] is fast_mode
                        for record in records
                    )
                )
                print(
                    json.dumps(
                        {
                            "stage": "client",
                            "fastMode": fast_mode,
                            "passed": passed,
                            "requests": records,
                        }
                    ),
                    flush=True,
                )
                if not passed:
                    raise SystemExit(
                        f"fastMode={fast_mode}: CC native Fast wire contract failed"
                    )
        finally:
            server.shutdown()
            thread.join()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claude", type=Path, default=Path.home() / ".local/bin/claude")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    verify_client(args.claude.expanduser().resolve(strict=True), args.timeout)


if __name__ == "__main__":
    main()
