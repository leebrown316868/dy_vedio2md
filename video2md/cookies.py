from __future__ import annotations

import re
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class CookieReport:
    count: int
    names: list[str]
    has_session_cookie: bool
    has_odin_tt: bool
    has_ttwid: bool


def inspect_cookie_header(text: str) -> CookieReport:
    pairs = _parse_cookie_pairs(text)
    names = [name for name, _ in pairs]
    return CookieReport(
        count=len(pairs),
        names=names,
        has_session_cookie=any(name in {"sessionid", "sessionid_ss", "sid_guard"} for name in names),
        has_odin_tt="odin_tt" in names,
        has_ttwid="ttwid" in names,
    )


def to_netscape_cookie_text(
    text: str,
    *,
    domain: str = ".douyin.com",
    expiry: int | None = None,
) -> str:
    expiry_value = str(expiry or int(time.time()) + 60 * 60 * 24 * 30)
    bare_domain = domain.lstrip(".")
    lines = ["# Netscape HTTP Cookie File"]
    for name, value in _parse_cookie_pairs(text):
        for cookie_domain, include_subdomains in ((domain, "TRUE"), (bare_domain, "FALSE")):
            lines.append(
                "\t".join(
                    [cookie_domain, include_subdomains, "/", "FALSE", expiry_value, name, value]
                )
            )
    return "\n".join(lines) + "\n"


def _parse_cookie_pairs(text: str) -> list[tuple[str, str]]:
    raw = _extract_cookie_header(text)
    pairs: list[tuple[str, str]] = []
    for part in raw.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        if not name:
            continue
        pairs.append((name, value.strip()))
    return pairs


def _extract_cookie_header(text: str) -> str:
    raw = text.strip()
    curl_match = re.search(r"(?:^|\s)-H\s+(['\"])Cookie:\s*(.*?)\1", raw, re.DOTALL)
    if curl_match:
        return curl_match.group(2).strip()
    if raw.lower().startswith("cookie:"):
        return raw.split(":", 1)[1].strip()
    if "Cookie:" in raw:
        raw = raw.split("Cookie:", 1)[1]
        for marker in ("\r\n", "\n", "'", '"'):
            raw = raw.split(marker, 1)[0]
    return raw.strip()
