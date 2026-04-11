#!/usr/bin/env python3
"""validate_actuator.py — actuator endpoint 동적 테스트 전 URL 안전성 검증.

Usage:
    python3 validate_actuator.py <URL>

Exit code:
    0 — 테스트 허용
    1 — 테스트 금지 (파괴적 endpoint)
"""
import sys, re
from urllib.parse import urlparse

FORBIDDEN_PATTERNS = [
    r"/actuator/shutdown",
    r"/actuator/refresh",
]


def is_forbidden(url):
    parsed = urlparse(url)
    path = parsed.path.rstrip("/").lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, path):
            return True, pattern
    return False, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_actuator.py <URL>", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    forbidden, matched = is_forbidden(url)
    if forbidden:
        print("이 endpoint는 동적 테스트가 금지되어 있습니다.", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"OK: {url}")
        sys.exit(0)
