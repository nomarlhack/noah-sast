#!/usr/bin/env python3
"""assemble_report.py — 스켈레톤과 서브에이전트 결과를 조립하여 MD 보고서를 생성한다.

Usage:
    이 스크립트는 scan-report 스킬의 Step 3에서 Bash로 실행된다.
    skeleton, subagent_results, chain_analysis를 Python 코드 내에서 직접 설정한 후 실행한다.

    python3 assemble_report.py

설계 원칙:
    요약 테이블은 상세 섹션에서 자동 생성한다 (단일 진실 원천).
    공격 시나리오 섹션은 chain_analysis 데이터에서 자동 생성한다.
"""
import json, os, re, sys

# --- 아래 변수를 실행 전에 설정한다 ---
skeleton = ""  # Step 1에서 작성한 스켈레톤
subagent_results = []  # 서브에이전트 반환 텍스트 목록
report_name = "noah-sast-report"  # 또는 "{scanner-type}-scan-report"

# chain_analysis: dict 또는 JSON 문자열
# {
#   "chains": [                              # 체인이 있을 때
#     {
#       "title": "체인 제목",
#       "attacker": "공격자 프로필",
#       "impact": "최종 영향",
#       "steps": [
#         {"vuln": "XSS-2", "desc": "설명"},
#         {"vuln": "SSRF-1", "desc": "설명"}
#       ],
#       "poc": "#### 재현 방법 및 POC\n\n**Step 1: ...**\n```bash\ncurl ...\n```"
#     }
#   ],
#   "independent": [                         # 체인에 포함되지 않은 후보
#     {"id": "XSS-2", "reason": "체인 미구성 사유"}
#   ]
# }
chain_analysis = None  # None이면 연계 분석 미수행, dict이면 수행됨
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


def build_chain_section(ca):
    """chain_analysis 데이터에서 ## 공격 시나리오 MD 섹션을 생성한다.

    Returns:
        str: 생성된 MD 텍스트. 연계 분석 미수행이면 빈 문자열.
    """
    if ca is None:
        return ''

    if isinstance(ca, str):
        ca = json.loads(ca)

    lines = ['## 공격 시나리오', '']

    chains = ca.get('chains', [])
    independent = ca.get('independent', [])

    if chains:
        for i, chain in enumerate(chains, 1):
            lines.append(f'### 체인 #{i}: {chain["title"]}')
            lines.append('')
            lines.append(f'**공격자 프로필**: {chain["attacker"]}')
            lines.append(f'**최종 영향**: {chain["impact"]}')
            lines.append('')
            lines.append('| Step | 취약점 | 설명 |')
            lines.append('|------|--------|------|')
            for j, step in enumerate(chain['steps'], 1):
                lines.append(f'| {j} | {step["vuln"]} | {step["desc"]} |')
            lines.append('')
            if chain.get('poc'):
                lines.append(chain['poc'])
                lines.append('')

        if independent:
            lines.append('### 독립 후보')
            lines.append('')

    if independent:
        lines.append('| 후보 | 체인 미구성 사유 |')
        lines.append('|------|----------------|')
        for item in independent:
            lines.append(f'| {item["id"]} | {item["reason"]} |')
        lines.append('')

    return '\n'.join(lines)


SKIP_PROJECT_SEGMENTS = {
    'src', 'lib', 'app', 'apps', 'packages', 'node_modules',
    'test', 'tests', 'config', 'public', 'static', 'build', 'dist',
}


def _extract_project(location):
    """위치 필드에서 프로젝트명을 추출한다. 추출 불가 시 None."""
    loc = location.strip().strip('`').split(',')[0].strip()
    parts = loc.split('/')
    if len(parts) >= 2 and parts[0] not in SKIP_PROJECT_SEGMENTS:
        return parts[0]
    return None


def build_table_from_details(report_text):
    """상세 섹션을 파싱하여 취약점 요약 테이블을 자동 생성한다.

    멀티 프로젝트 감지 시 '프로젝트' 컬럼을 자동 추가하고,
    <!-- PROJECT_SUMMARY_HERE --> 플레이스홀더를 프로젝트별 요약 테이블로 치환한다.
    """
    lines = report_text.split('\n')

    in_scanner_section = False
    current_scanner = ''
    vulns = []  # (title, type, scanner, status, project)
    current_vuln_title = None
    current_type = ''
    current_status = ''
    current_location = ''

    for line in lines:
        if line.startswith('## 스캐너별 실행 결과'):
            in_scanner_section = True
            continue
        if line.startswith('## ') and in_scanner_section:
            if current_vuln_title:
                proj = _extract_project(current_location)
                vulns.append((current_vuln_title, current_type, current_scanner, current_status, proj))
                current_vuln_title = None
                current_type = ''
                current_status = ''
                current_location = ''
            in_scanner_section = False
            continue

        if not in_scanner_section:
            continue

        m_scanner = re.match(r'^###\s+(.+?)\s*$', line)
        if m_scanner and not re.match(r'^###\s+\d+\.', line):
            if current_vuln_title:
                proj = _extract_project(current_location)
                vulns.append((current_vuln_title, current_type, current_scanner, current_status, proj))
                current_vuln_title = None
                current_type = ''
                current_status = ''
                current_location = ''
            scanner_name = m_scanner.group(1).strip()
            parts = [p.strip() for p in scanner_name.split('/')]
            parts = [re.sub(r'\s+', '-', p.lower()) for p in parts]
            current_scanner = ' / '.join(parts)
            continue

        m_vuln = re.match(r'^#{2,4}\s+(\d+)\.\s+(.+)$', line)
        if m_vuln:
            if current_vuln_title:
                proj = _extract_project(current_location)
                vulns.append((current_vuln_title, current_type, current_scanner, current_status, proj))
            current_vuln_title = m_vuln.group(2).strip()
            current_type = ''
            current_status = ''
            current_location = ''
            continue

        m_type = re.match(r'^\*\*유형:?\*\*\s*:?\s*(.+)$', line)
        if m_type and current_vuln_title:
            current_type = m_type.group(1).strip()
            continue

        m_status = re.match(r'^\*\*상태:?\*\*\s*:?\s*(.+)$', line)
        if m_status and current_vuln_title:
            raw = m_status.group(1).strip()
            current_status = '확인됨' if '확인됨' in raw else '후보'
            continue

        m_loc = re.match(r'^\*\*위치:?\*\*\s*:?\s*(.+)$', line)
        if m_loc and current_vuln_title and not current_location:
            current_location = m_loc.group(1).strip()
            continue

    if current_vuln_title:
        proj = _extract_project(current_location)
        vulns.append((current_vuln_title, current_type, current_scanner, current_status, proj))

    if not vulns:
        return report_text

    # 멀티 프로젝트 감지
    projects = [v[4] for v in vulns if v[4]]
    unique_projects = sorted(set(projects))
    is_multi = len(unique_projects) >= 2

    # 헤딩 재번호
    heading_pat = re.compile(r'^(#{2,4})\s+\d+\.\s+(.+)$', re.MULTILINE)
    matches = list(heading_pat.finditer(report_text))
    result = report_text
    for new_num, m in enumerate(reversed(matches), 1):
        actual_num = len(matches) - new_num + 1
        hashes = m.group(1)
        title = m.group(2)
        result = result[:m.start()] + f'{hashes} {actual_num}. {title}' + result[m.end():]

    # 요약 테이블 생성
    if is_multi:
        table_lines = [
            '| # | 취약점 제목 | 유형 | 프로젝트 | 스캐너 | 상태 |',
            '|---|------------|------|----------|--------|------|',
        ]
        for idx, (title, vtype, scanner, status, proj) in enumerate(vulns, 1):
            proj_label = proj or '전체'
            table_lines.append(f'| {idx} | {title} | {vtype} | {proj_label} | {scanner} | {status} |')
    else:
        table_lines = [
            '| # | 취약점 제목 | 유형 | 스캐너 | 상태 |',
            '|---|------------|------|--------|------|',
        ]
        for idx, (title, vtype, scanner, status, _proj) in enumerate(vulns, 1):
            table_lines.append(f'| {idx} | {title} | {vtype} | {scanner} | {status} |')
    new_table = '\n'.join(table_lines)

    tbl_section = re.search(
        r'(## 취약점 요약 테이블\s*\n\s*\n)'
        r'(\|[^\n]+\n'
        r'\|[^\n]+\n'
        r'(?:\|[^\n]+\n)*)',
        result
    )
    if tbl_section:
        result = result[:tbl_section.start(2)] + new_table + '\n' + result[tbl_section.end(2):]

    # 프로젝트별 요약 테이블 생성 (멀티 프로젝트일 때만)
    if is_multi and '<!-- PROJECT_SUMMARY_HERE -->' in result:
        proj_counts = {}
        for _t, _tp, _s, status, proj in vulns:
            key = proj or '전체/인프라'
            if key not in proj_counts:
                proj_counts[key] = {'확인됨': 0, '후보': 0}
            proj_counts[key][status] += 1

        plines = ['## 프로젝트별 요약', '',
                   '| 프로젝트 | 확인됨 | 후보 | 합계 |',
                   '|----------|--------|------|------|']
        for pname in sorted(proj_counts.keys()):
            c = proj_counts[pname]
            total = c['확인됨'] + c['후보']
            plines.append(f'| {pname} | {c["확인됨"]}건 | {c["후보"]}건 | {total}건 |')
        plines.append('')
        result = result.replace('<!-- PROJECT_SUMMARY_HERE -->', '\n'.join(plines))
    else:
        result = result.replace('<!-- PROJECT_SUMMARY_HERE -->', '')

    return result


if __name__ == '__main__':
    sections_text = '\n\n---\n\n'.join(clean_section(s) for s in subagent_results)
    full_report = skeleton.replace('<!-- SCANNER_SECTIONS_HERE -->', sections_text)

    # 공격 시나리오 섹션 자동 생성
    chain_md = build_chain_section(chain_analysis)
    full_report = full_report.replace('<!-- CHAIN_SECTION_HERE -->', chain_md)

    # 상세 섹션에서 요약 테이블 자동 생성 + 헤딩 재번호
    full_report = build_table_from_details(full_report)

    md_path = f'{report_name}.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(full_report)

    poc = full_report.count('재현 방법 및 POC')
    has_chain = '## 공격 시나리오' in full_report
    print(f"조립 완료: {os.path.getsize(md_path)} bytes, POC {poc}건, 공격시나리오={'✓' if has_chain else '✗'}")
