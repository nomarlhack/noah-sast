#!/usr/bin/env python3
"""assemble_report.py — 스켈레톤과 서브에이전트 결과를 조립하여 MD 보고서를 생성한다.

Usage:
    이 스크립트는 scan-report 스킬의 Step 3에서 Bash로 실행된다.
    skeleton과 subagent_results를 Python 코드 내에서 직접 설정한 후 실행한다.

    python3 assemble_report.py

설계 원칙:
    요약 테이블은 상세 섹션에서 자동 생성한다 (단일 진실 원천).
    스켈레톤의 취약점 요약 테이블은 무시되고 상세 섹션에서 파싱한 데이터로 대체된다.
"""
import os, re, sys

# --- 아래 변수를 실행 전에 설정한다 ---
skeleton = ""  # Step 1에서 작성한 스켈레톤
subagent_results = []  # 서브에이전트 반환 텍스트 목록
report_name = "noah-sast-report"  # 또는 "{scanner-type}-scan-report"
# -----------------------------------

def normalize_vuln_headings(text):
    """**N번 ...**: 제목 형식을 #### N. 제목 헤딩으로 정규화."""
    def replace_heading(m):
        num = m.group(1)
        title = m.group(2).strip().rstrip('*').strip()
        return f'#### {num}. {title}'
    text = re.sub(
        r'^\*\*(\d+)번\s*(?:\([^)]+\))?\s*[-–]\s*[A-Za-z0-9_-]+:\s*(.+?)\*{0,2}\s*$',
        replace_heading, text, flags=re.MULTILINE)
    text = re.sub(
        r'^\*\*(\d+)번\s*[-–]\s*[A-Za-z0-9_-]+\*\*:\s*(.+)$',
        replace_heading, text, flags=re.MULTILINE)
    return text

def clean_section(text):
    """## 레벨 헤딩 제거 + 취약점 헤딩 정규화."""
    text = normalize_vuln_headings(text)
    lines = text.split('\n')
    return '\n'.join(l for l in lines if not l.startswith('## '))

def build_table_from_details(report_text):
    """상세 섹션을 파싱하여 취약점 요약 테이블을 자동 생성한다.

    각 #### N. 제목 헤딩 아래의 **유형**: 과 **상태**: 필드,
    그리고 상위 ### Scanner 헤딩에서 스캐너명을 추출한다.
    """
    lines = report_text.split('\n')

    # 스캐너별 실행 결과 섹션 내부에서만 파싱
    in_scanner_section = False
    current_scanner = ''
    vulns = []  # [(title, vuln_type, scanner, status)]
    current_vuln_title = None
    current_type = ''
    current_status = ''

    for line in lines:
        # 섹션 진입/이탈
        if line.startswith('## 스캐너별 실행 결과'):
            in_scanner_section = True
            continue
        if line.startswith('## ') and in_scanner_section:
            # 다음 ## 섹션 → 스캐너 결과 영역 종료
            if current_vuln_title:
                vulns.append((current_vuln_title, current_type, current_scanner, current_status))
                current_vuln_title = None
                current_type = ''
                current_status = ''
            in_scanner_section = False
            continue

        if not in_scanner_section:
            continue

        # ### Scanner Name 헤딩
        m_scanner = re.match(r'^###\s+(.+?)\s*$', line)
        if m_scanner and not re.match(r'^###\s+\d+\.', line):
            if current_vuln_title:
                vulns.append((current_vuln_title, current_type, current_scanner, current_status))
                current_vuln_title = None
                current_type = ''
                current_status = ''
            scanner_name = m_scanner.group(1).strip()
            # "XSS / DOM-XSS / Open Redirect Scanner" → "xss / dom-xss / open-redirect"
            # 각 부분을 개별 kebab-case로 변환하고 " / "로 연결
            parts = [p.strip() for p in scanner_name.split('/')]
            parts = [re.sub(r'\s+', '-', p.lower()) for p in parts]
            current_scanner = ' / '.join(parts)
            continue

        # #### N. 취약점 제목 (또는 ### N. 또는 ## N.)
        m_vuln = re.match(r'^#{2,4}\s+(\d+)\.\s+(.+)$', line)
        if m_vuln:
            if current_vuln_title:
                vulns.append((current_vuln_title, current_type, current_scanner, current_status))
            current_vuln_title = m_vuln.group(2).strip()
            current_type = ''
            current_status = ''
            continue

        # **유형**: ...
        m_type = re.match(r'^\*\*유형\*\*\s*:\s*(.+)$', line)
        if m_type and current_vuln_title:
            current_type = m_type.group(1).strip()
            continue

        # **상태**: ...
        m_status = re.match(r'^\*\*상태\*\*\s*:\s*(.+)$', line)
        if m_status and current_vuln_title:
            raw = m_status.group(1).strip()
            # "후보 (추가 검증 필요)" → "후보"
            if '확인됨' in raw:
                current_status = '확인됨'
            else:
                current_status = '후보'
            continue

    # 마지막 항목
    if current_vuln_title:
        vulns.append((current_vuln_title, current_type, current_scanner, current_status))

    if not vulns:
        return report_text

    # 헤딩 재번호 (1부터)
    heading_pat = re.compile(r'^(#{2,4})\s+\d+\.\s+(.+)$', re.MULTILINE)
    matches = list(heading_pat.finditer(report_text))
    result = report_text
    for new_num, m in enumerate(reversed(matches), 1):
        actual_num = len(matches) - new_num + 1
        hashes = m.group(1)
        title = m.group(2)
        result = result[:m.start()] + f'{hashes} {actual_num}. {title}' + result[m.end():]

    # 요약 테이블 생성
    table_lines = [
        '| # | 취약점 제목 | 유형 | 스캐너 | 상태 |',
        '|---|------------|------|--------|------|',
    ]
    for idx, (title, vtype, scanner, status) in enumerate(vulns, 1):
        table_lines.append(f'| {idx} | {title} | {vtype} | {scanner} | {status} |')
    new_table = '\n'.join(table_lines)

    # 기존 요약 테이블 영역을 새 테이블로 교체
    # 패턴: "## 취약점 요약 테이블" 다음의 테이블 영역
    tbl_section = re.search(
        r'(## 취약점 요약 테이블\s*\n\s*\n)'   # 헤더 + 빈줄
        r'(\|[^\n]+\n'                           # 테이블 헤더
        r'\|[^\n]+\n'                            # 구분선
        r'(?:\|[^\n]+\n)*)',                     # 데이터 행들
        result
    )
    if tbl_section:
        result = result[:tbl_section.start(2)] + new_table + '\n' + result[tbl_section.end(2):]

    return result


if __name__ == '__main__':
    sections_text = '\n\n---\n\n'.join(clean_section(s) for s in subagent_results)
    full_report = skeleton.replace('<!-- SCANNER_SECTIONS_HERE -->', sections_text)

    # 상세 섹션에서 요약 테이블 자동 생성 + 헤딩 재번호
    full_report = build_table_from_details(full_report)

    md_path = f'{report_name}.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(full_report)

    poc = full_report.count('재현 방법 및 POC')
    print(f"조립 완료: {os.path.getsize(md_path)} bytes, POC {poc}건")
