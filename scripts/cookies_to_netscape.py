from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from video2md.cookies import inspect_cookie_header, to_netscape_cookie_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a Cookie header to a Netscape cookies.txt file.")
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--domain", default=".douyin.com")
    args = parser.parse_args()

    raw = args.source.read_text(encoding="utf-8", errors="ignore")
    report = inspect_cookie_header(raw)
    args.target.parent.mkdir(parents=True, exist_ok=True)
    args.target.write_text(to_netscape_cookie_text(raw, domain=args.domain), encoding="utf-8")
    print(f"converted {report.count} cookie names")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
