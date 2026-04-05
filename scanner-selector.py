#!/usr/bin/env python3
"""scanner-selector.py — grep 인덱스 + 프로젝트 파일 기반 스캐너 자동 선별.

Usage:
    python3 scanner-selector.py <PATTERN_INDEX_DIR> <PROJECT_ROOT>

Output:
    - 적용 스캐너 목록 (grep 히트 건수 포함)
    - 제외 스캐너 목록 (제외 사유 포함)
"""
import json, os, sys, glob

if len(sys.argv) < 3:
    print("Usage: python3 scanner-selector.py <PATTERN_INDEX_DIR> <PROJECT_ROOT>")
    sys.exit(1)

INDEX_DIR = sys.argv[1]
PROJECT_ROOT = sys.argv[2]

# --- Helper: 프로젝트 파일 존재 여부 ---
def has_file(*patterns):
    for p in patterns:
        if glob.glob(os.path.join(PROJECT_ROOT, p)) or glob.glob(os.path.join(PROJECT_ROOT, "**", p), recursive=True):
            return True
    return False

def read_pkg_json():
    pkg_path = os.path.join(PROJECT_ROOT, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def has_dependency(pkg, *names):
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    return any(n in deps for n in names)

# --- grep 인덱스 읽기 ---
def read_index(scanner_name):
    path = os.path.join(INDEX_DIR, f"{scanner_name}.json")
    if not os.path.exists(path):
        return {}, 0
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    total = sum(len(v) for v in data.values())
    return data, total

# --- 스캐너 제외 조건 (grep 0건일 때만 적용) ---
SCANNERS = [
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
    "websocket-scanner", "subdomain-takeover-scanner", "idor-scanner"
]

pkg = read_pkg_json()
has_requirements = has_file("requirements.txt", "Pipfile", "pyproject.toml")
has_gemfile = has_file("Gemfile")
has_pom = has_file("pom.xml", "build.gradle")

def check_exclude(scanner):
    """grep 0건일 때 아키텍처 조건으로 제외 가능한지 확인. 제외 시 사유 반환, 포함 시 None."""
    if scanner == "xss-scanner":
        if not has_file("*.html", "*.erb", "*.slim", "*.jsx", "*.tsx", "*.vue"):
            return "HTML 출력이 전혀 없는 프로젝트"
    elif scanner == "dom-xss-scanner":
        if not has_file("*.js", "*.jsx", "*.ts", "*.tsx", "*.vue"):
            return "프론트엔드 JS 코드 없음"
    elif scanner == "ssrf-scanner":
        if not has_dependency(pkg, "axios", "node-fetch", "got", "request", "urllib3", "requests", "httpx"):
            return "서버사이드 HTTP 요청 라이브러리 없음"
    elif scanner == "csrf-scanner":
        if has_dependency(pkg, "jsonwebtoken", "jose") and not has_file("*.erb", "*.html"):
            return "쿠키 기반 인증 아님 (토큰 전용 API)"
    elif scanner == "file-upload-scanner":
        if not has_dependency(pkg, "multer", "busboy", "formidable", "multiparty"):
            if not has_requirements and not has_gemfile:
                return "파일 업로드 엔드포인트 없음"
    elif scanner == "command-injection-scanner":
        pass  # grep이 0이면 exec/system 호출 없으므로 안전
    elif scanner == "sqli-scanner":
        if not has_dependency(pkg, "mysql", "mysql2", "pg", "better-sqlite3", "sequelize", "knex", "typeorm", "prisma"):
            if not has_requirements and not has_gemfile and not has_pom:
                return "SQL 라이브러리/ORM 없음"
    elif scanner == "xxe-scanner":
        if not has_dependency(pkg, "xml2js", "fast-xml-parser", "libxmljs", "sax", "xmldom"):
            if not has_requirements and not has_pom:
                return "XML 파싱 라이브러리 없음"
    elif scanner == "deserialization-scanner":
        pass  # grep이 0이면 역직렬화 함수 호출 없음
    elif scanner == "ssti-scanner":
        if not has_dependency(pkg, "ejs", "pug", "handlebars", "nunjucks", "mustache"):
            if not has_requirements and not has_gemfile:
                return "서버사이드 템플릿 엔진 없음"
    elif scanner == "jwt-scanner":
        if not has_dependency(pkg, "jsonwebtoken", "jose", "jwt-decode", "jwks-rsa"):
            return "JWT 라이브러리 없음"
    elif scanner == "oauth-scanner":
        if not has_dependency(pkg, "passport", "passport-oauth2", "openid-client", "oauth", "grant"):
            return "OAuth/OIDC 라이브러리 없음"
    elif scanner == "nosqli-scanner":
        if not has_dependency(pkg, "mongoose", "mongodb", "mongoist"):
            return "NoSQL 라이브러리 없음"
    elif scanner == "ldap-injection-scanner":
        if not has_dependency(pkg, "ldapjs", "ldap-authentication", "activedirectory"):
            if not has_requirements:
                return "LDAP 라이브러리 없음"
    elif scanner == "xslt-injection-scanner":
        if not has_dependency(pkg, "xslt", "saxon", "libxslt"):
            return "XSLT 라이브러리 없음"
    elif scanner == "xpath-injection-scanner":
        if not has_dependency(pkg, "xpath", "xmldom", "libxmljs"):
            return "XPath 라이브러리 없음"
    elif scanner == "soapaction-spoofing-scanner":
        if not has_dependency(pkg, "soap", "strong-soap"):
            if not has_file("*.wsdl"):
                return "SOAP 라이브러리/WSDL 없음"
    elif scanner == "pdf-generation-scanner":
        if not has_dependency(pkg, "puppeteer", "wkhtmltopdf", "pdfkit", "html-pdf", "playwright"):
            return "PDF 생성 라이브러리 없음"
    elif scanner == "saml-scanner":
        if not has_dependency(pkg, "saml2-js", "passport-saml", "samlify", "node-saml"):
            return "SAML 라이브러리 없음"
    elif scanner == "zipslip-scanner":
        if not has_dependency(pkg, "adm-zip", "unzipper", "yauzl", "tar", "archiver"):
            return "압축 해제 라이브러리 없음"
    elif scanner == "graphql-scanner":
        if not has_dependency(pkg, "graphql", "apollo-server", "express-graphql", "mercurius"):
            return "GraphQL 라이브러리 없음"
    elif scanner == "sourcemap-scanner":
        if not has_dependency(pkg, "webpack", "vite", "esbuild", "rollup", "parcel"):
            return "프론트엔드 빌드 도구 없음"
    elif scanner == "csv-injection-scanner":
        if not has_dependency(pkg, "csv-writer", "csv-stringify", "exceljs", "xlsx", "papaparse"):
            return "CSV/Excel 라이브러리 없음"
    elif scanner == "prototype-pollution-scanner":
        if not has_file("*.js", "*.ts", "*.mjs"):
            return "JavaScript/Node.js 프로젝트 아님"
    elif scanner == "websocket-scanner":
        if not has_dependency(pkg, "ws", "socket.io", "sockjs", "faye-websocket"):
            return "WebSocket 라이브러리 없음"
    elif scanner == "subdomain-takeover-scanner":
        if not has_file("*.tf", "CNAME", "dns*"):
            return "DNS/인프라 설정 없음"
    # open-redirect, crlf, path-traversal, http-method-tampering, host-header,
    # css-injection, redos, http-smuggling, idor: 아키텍처만으로 제외하기 어려움 → 포함
    return None

# --- 선별 실행 ---
included = []
excluded = []

print("=" * 60)
print("스캐너 선별 결과")
print("=" * 60)
print()
print("| 스캐너 | grep 히트 | 판정 | 사유 |")
print("|--------|----------|------|------|")

for scanner in SCANNERS:
    _, count = read_index(scanner)
    if count > 0:
        included.append((scanner, count))
        print(f"| {scanner} | {count} | ✅ 포함 | grep 히트 {count}건 |")
    else:
        reason = check_exclude(scanner)
        if reason:
            excluded.append((scanner, reason))
            print(f"| {scanner} | 0 | ❌ 제외 | {reason} |")
        else:
            included.append((scanner, 0))
            print(f"| {scanner} | 0 | ✅ 포함 | 아키텍처 제외 조건 미충족 |")

print()
print(f"적용: {len(included)}개 / 제외: {len(excluded)}개 / 전체: {len(SCANNERS)}개")
print()
print("--- 적용 스캐너 목록 ---")
for s, c in included:
    print(s)
