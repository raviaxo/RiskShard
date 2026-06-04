#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.web_console import build_server  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Start the local RiskShard browser console.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument(
        "--root",
        default=ROOT,
        type=Path,
        help="Repository root to use for scenarios, evidence, and results.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    server = build_server(host=args.host, port=args.port, root=args.root)
    url = f"http://{args.host}:{args.port}/"
    print(f"RiskShard browser console: {url}")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping RiskShard browser console.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
