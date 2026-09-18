from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from video2md.cookies import inspect_cookie_header, to_netscape_cookie_text

FIREFOX_PROFILES = Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"


def find_profile(explicit: Path | None) -> Path:
    if explicit:
        if not (explicit / "cookies.sqlite").is_file():
            raise SystemExit(f"No cookies.sqlite under {explicit}")
        return explicit
    candidates = [p for p in FIREFOX_PROFILES.glob("*/cookies.sqlite") if p.is_file()]
    if not candidates:
        raise SystemExit(f"No Firefox cookie database found under {FIREFOX_PROFILES}")
    return max(candidates, key=lambda p: p.stat().st_mtime).parent


def read_cookie_header(profile: Path, domain: str) -> str:
    db = profile / "cookies.sqlite"
    # immutable=1 allows reading while Firefox is running.
    con = sqlite3.connect(f"file:{db}?immutable=1", uri=True)
    try:
        # Shortest host first so ".douyin.com" wins over "www.douyin.com".
        rows = con.execute(
            "SELECT name, value FROM moz_cookies WHERE host LIKE ? ORDER BY length(host)",
            (f"%{domain}%",),
        ).fetchall()
    finally:
        con.close()
    seen: dict[str, str] = {}
    for name, value in rows:
        seen.setdefault(name, value)
    return "; ".join(f"{name}={value}" for name, value in seen.items())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a cookie string from a local Firefox profile, without manual export.",
    )
    parser.add_argument("domain", help="e.g. douyin.com or bilibili.com")
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument(
        "--format",
        choices=("header", "netscape"),
        default="header",
        help="header = raw 'k=v; k=v' (DouK); netscape = yt-dlp --cookies format.",
    )
    parser.add_argument("--profile", type=Path, help="Firefox profile dir; defaults to most recently used.")
    args = parser.parse_args()

    profile = find_profile(args.profile)
    header = read_cookie_header(profile, args.domain)
    if not header:
        raise SystemExit(f"No cookies found for {args.domain} in {profile}")

    report = inspect_cookie_header(header)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "netscape":
        text = to_netscape_cookie_text(header, domain=f".{args.domain}")
    else:
        text = header + "\n"
    args.output.write_text(text, encoding="utf-8")

    print(f"profile: {profile}")
    print(f"wrote {report.count} cookie names to {args.output} ({args.format})")
    print(f"names: {', '.join(report.names)}")
    print(
        "checks: "
        f"session={report.has_session_cookie} "
        f"odin_tt={report.has_odin_tt} "
        f"ttwid={report.has_ttwid}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
