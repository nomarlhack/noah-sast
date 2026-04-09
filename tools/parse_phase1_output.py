#!/usr/bin/env python3
"""parse_phase1_output.py — Phase 1 그룹 에이전트 출력을 스캐너별로 파싱한다.

메인 에이전트가 그룹 에이전트 반환값을 이 스크립트에 전달하면,
스캐너별 섹션을 분리하여 JSON 배열로 반환한다.

Usage (stdin):
    echo "$AGENT_OUTPUT" | python3 parse_phase1_output.py

Usage (file):
    python3 parse_phase1_output.py output.txt

출력: JSON 배열 [{"scanner": "xss-scanner", "content": "..."}, ...]

하위 호환: ===SCANNER_BOUNDARY=== 외에 === scanner-name === 레거시 형식도 지원.
"""
import json
import re
import sys
from difflib import get_close_matches

KNOWN_SCANNERS = [
    "xss-scanner", "dom-xss-scanner", "ssrf-scanner", "open-redirect-scanner",
    "crlf-injection-scanner", "csrf-scanner", "path-traversal-scanner",
    "file-upload-scanner", "command-injection-scanner", "sqli-scanner",
    "http-method-tampering-scanner", "xxe-scanner", "deserialization-scanner",
    "ssti-scanner", "jwt-scanner", "oauth-scanner", "nosqli-scanner",
    "ldap-injection-scanner", "host-header-scanner", "xslt-injection-scanner",
    "css-injection-scanner", "xpath-injection-scanner", "soapaction-spoofing-scanner",
    "redos-scanner", "pdf-generation-scanner", "saml-scanner",
    "http-smuggling-scanner", "zipslip-scanner", "graphql-scanner",
    "sourcemap-scanner", "csv-injection-scanner", "prototype-pollution-scanner",
    "websocket-scanner", "subdomain-takeover-scanner", "idor-scanner",
    "business-logic-scanner", "security-headers-scanner",
]

# 정규식: ===SCANNER_BOUNDARY=== 또는 === <name> === (레거시)
BOUNDARY_RE = re.compile(r"^===\s*SCANNER_BOUNDARY\s*===$", re.MULTILINE)
LEGACY_BOUNDARY_RE = re.compile(r"^===\s*(.+?)\s*===$", re.MULTILINE)
TAG_RE = re.compile(r"^\[([a-z0-9_-]+(?:-scanner)?)\]\s*$", re.MULTILINE)


def normalize_scanner_name(raw_name):
    """스캐너명을 정규화하여 KNOWN_SCANNERS와 매칭."""
    name = raw_name.strip().lower()
    name = re.sub(r"\s+", "-", name)
    # "XSS Scanner" → "xss-scanner"
    if not name.endswith("-scanner") and name + "-scanner" in KNOWN_SCANNERS:
        name = name + "-scanner"
    # 정확히 매칭
    if name in KNOWN_SCANNERS:
        return name
    # fuzzy match
    matches = get_close_matches(name, KNOWN_SCANNERS, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    return name  # 매칭 실패 시 원본 반환


def parse_output(text):
    """그룹 에이전트 출력을 스캐너별로 분리."""
    sections = []

    # 1차 시도: ===SCANNER_BOUNDARY=== 로 분리
    parts = BOUNDARY_RE.split(text)
    if len(parts) > 1:
        for part in parts:
            part = part.strip()
            if not part:
                continue
            tag_match = TAG_RE.match(part)
            if tag_match:
                scanner = normalize_scanner_name(tag_match.group(1))
                content = part[tag_match.end():].strip()
                sections.append({"scanner": scanner, "content": content})
            else:
                # 태그 없이 내용만 있는 경우 — 스캐너명 추론 시도
                sections.append({"scanner": "_unknown", "content": part})
        if sections:
            return sections

    # 2차 시도: === scanner-name === 레거시 형식
    legacy_parts = LEGACY_BOUNDARY_RE.split(text)
    if len(legacy_parts) > 1:
        # split 결과: [앞부분, 캡처1, 내용1, 캡처2, 내용2, ...]
        i = 1
        while i < len(legacy_parts):
            scanner = normalize_scanner_name(legacy_parts[i])
            content = legacy_parts[i + 1].strip() if i + 1 < len(legacy_parts) else ""
            sections.append({"scanner": scanner, "content": content})
            i += 2
        return sections

    # 둘 다 실패 — 전체를 하나의 섹션으로 반환
    return [{"scanner": "_unparsed", "content": text.strip()}]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    result = parse_output(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 요약
    parsed = [s for s in result if s["scanner"] != "_unparsed"]
    unknown = [s for s in result if s["scanner"] == "_unknown"]
    if unknown:
        print(f"\nWARNING: {len(unknown)} section(s) without scanner tag", file=sys.stderr)
    if not parsed and result[0]["scanner"] == "_unparsed":
        print("\nERROR: No scanner boundaries found — output could not be parsed", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\nParsed {len(parsed)} scanner section(s)", file=sys.stderr)
