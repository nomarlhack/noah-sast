import html as html_mod, re, sys, os

_base = os.getcwd()
_skill_dir = os.path.dirname(os.path.abspath(__file__))
_md_path = os.path.join(_base, 'noah-sast-report.md')
_html_path = os.path.join(_base, 'noah-sast-report.html')

with open(_md_path, encoding='utf-8') as f:
    _md_text = f.read()

# --- 리뷰 섹션 자동 제거 (scan-report-review 산출물이 잔류한 경우) ---
_md_text = re.sub(r'\n## (?:보고서 )?(?:리뷰|검증) 결과.*?(?=\n## |\Z)', '', _md_text, flags=re.DOTALL)

# --- 변환 전 요약 테이블·총괄 요약 자동 동기화 ---
# assemble_report.py 의 build_table_from_details 를 임포트하여
# 상세 섹션 → 요약 테이블을 항상 재생성한��.
sys.path.insert(0, _skill_dir)
from assemble_report import build_table_from_details
_md_text = build_table_from_details(_md_text)

# 총괄 요약의 확인됨/후보 건수도 요약 테이블에서 재집계
def _sync_dashboard(md):
    tbl = re.search(r'## 취약점 요약 테이블\s*\n\s*\n((?:\|.*\n)+)', md)
    if not tbl:
        return md
    rows = tbl.group(1)
    confirmed = len(re.findall(r'\|\s*확인됨\s*\|', rows))
    candidate = len(re.findall(r'\|\s*후보\s*\|', rows))
    # 총괄 요약 섹션만 추출하여 그 범위 안에서만 치환
    dashboard_match = re.search(r'(## 총괄 요약\s*\n\s*\n(?:\|.*\n)+)', md)
    if not dashboard_match:
        return md
    old_block = dashboard_match.group(1)
    new_block = re.sub(r'(\|\s*(?:확인된 취약점|확인됨)\s*\|\s*)\d+(?:건)?', rf'\g<1>{confirmed}건', old_block)
    new_block = re.sub(r'(\|\s*후보[^|]*\|\s*)\d+(?:건)?', rf'\g<1>{candidate}건', new_block)
    return md.replace(old_block, new_block, 1)

_md_text = _sync_dashboard(_md_text)

# 동기화된 MD 를 디스크에도 반영 (단일 진실 원천)
with open(_md_path, 'w', encoding='utf-8') as f:
    f.write(_md_text)

lines = [l.rstrip('\n') for l in _md_text.splitlines()]

# 대시보드 수치를 MD에서 동적으로 집계 (suffix 유무 모두 허용, 첫 셀에 괄호 수식어 허용)
def _parse_dashboard(md):
    confirmed = candidate = safe = na = 0
    # 첫 셀이 "확인된 취약점" 또는 "확인됨"으로 시작하면 매칭 (괄호 수식어 허용)
    m = re.search(r'\|\s*(?:확인된 취약점|확인됨)[^|]*\|\s*(\d+)(?:건)?', md)
    if m: confirmed = int(m.group(1))
    m = re.search(r'\|\s*후보[^|]*\|\s*(\d+)(?:건)?', md)
    if m: candidate = int(m.group(1))
    # "스캔 완료 (이상 없음)", "이상 없음 스캐너", "이상 없음" 등 괄호/후행 단어 모두 허용
    m = re.search(r'\|\s*(?:스캔 완료|이상 없음)[^|]*\|\s*(\d+)(?:개)?', md)
    if m: safe = int(m.group(1))
    # "해당 없음 (미적용)", "미적용 스캐너", "미적용" 등 허용
    m = re.search(r'\|\s*(?:해당 없음|미적용)[^|]*\|\s*(\d+)(?:개)?', md)
    if m: na = int(m.group(1))
    return confirmed, candidate, safe, na

_confirmed, _candidate, _safe, _na = _parse_dashboard(_md_text)

def esc(text):
    return html_mod.escape(text)

def inline(text):
    t = esc(text)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    return t

CSS = '''
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1100px;margin:0 auto;padding:32px 24px;color:#1a1a2e;background:#f0f2f5}
h1{color:#1a1a2e;font-size:1.75em;font-weight:800;border:none;padding-bottom:0;margin-bottom:4px}
h1+p,h1+hr{margin-top:6px}
h2{color:#1a1a2e;margin-top:0;font-size:1.15em;font-weight:700;letter-spacing:-0.01em}
h3{color:#1a1a2e;margin-top:18px;font-size:1em;font-weight:600}
h3.scanner-heading,.chain-card>h3,details.vuln-block>summary h3{color:#2563eb}
h4{color:#374151;margin-top:16px;font-size:0.92em;font-weight:600}
h5{color:#4b5563;margin-top:12px;font-size:0.88em;font-weight:600}
table{border-collapse:collapse;width:100%;margin:14px 0;background:white;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06),0 0 0 1px rgba(0,0,0,.04)}
th{background:#1e293b;color:#f1f5f9;padding:11px 16px;text-align:left;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.04em}
td{padding:10px 16px;border-bottom:1px solid #f1f5f9;font-size:13px;color:#334155}
tr:last-child td{border-bottom:none}
tr:nth-child(even){background:#f8fafc}
tr:hover{background:#eef2ff}
pre{background:#0f172a;color:#e2e8f0;padding:18px 20px;border-radius:10px;overflow-x:auto;font-size:12.5px;line-height:1.6;border:1px solid #1e293b}
code{background:#e0e7ff;color:#3730a3;padding:2px 6px;border-radius:4px;font-size:12px;font-family:'JetBrains Mono','SF Mono',Consolas,monospace}
pre code{background:none;padding:0;color:inherit}
details.scanner-block{background:white;border:1px solid #e2e8f0;border-radius:12px;margin:14px 0;box-shadow:0 1px 4px rgba(0,0,0,.04)}
details.scanner-block>summary{cursor:pointer;padding:16px 20px;font-weight:600;user-select:none;list-style:none;transition:background .15s}
details.scanner-block>summary:hover{background:#f8fafc}
details.scanner-block>summary::-webkit-details-marker{display:none}
details.scanner-block>summary::before{content:'▸ ';font-size:13px;color:#2563eb;font-weight:700}
details.scanner-block[open]>summary::before{content:'▾ '}
details.scanner-block[open]>summary{border-bottom:1px solid #e2e8f0}
details.scanner-block>summary h2{display:inline;font-size:1.05em;margin:0}
.scanner-body{padding:8px 20px 20px}
details.vuln-block{background:white;border:1px solid #e2e8f0;border-left:4px solid #2563eb;margin:16px 0;border-radius:8px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
details.vuln-block>summary{cursor:pointer;padding:12px 16px;list-style:none;transition:background .15s}
details.vuln-block>summary:hover{background:#f8fafc}
details.vuln-block>summary::-webkit-details-marker{display:none}
details.vuln-block>summary::before{content:'▸ ';font-size:11px;color:#2563eb;font-weight:700}
details.vuln-block[open]>summary::before{content:'▾ '}
details.vuln-block[open]>summary{border-bottom:1px solid #f1f5f9}
details.vuln-block>summary h3{display:inline;font-size:0.95em;margin:0;color:#1e40af}
.vuln-body{padding:8px 16px 16px}
details.chain-block{background:white;border:1px solid #e2e8f0;border-radius:12px;margin:14px 0;box-shadow:0 1px 4px rgba(0,0,0,.04)}
details.chain-block>summary{cursor:pointer;padding:16px 20px;font-weight:600;user-select:none;list-style:none;transition:background .15s}
details.chain-block>summary:hover{background:#f8fafc}
details.chain-block>summary::-webkit-details-marker{display:none}
details.chain-block>summary::before{content:'▸ ';font-size:13px;color:#dc2626;font-weight:700}
details.chain-block[open]>summary::before{content:'▾ '}
details.chain-block[open]>summary{border-bottom:1px solid #e2e8f0}
details.chain-block>summary h2{display:inline;font-size:1.05em;margin:0}
.chain-body{padding:8px 20px 20px}
details.chain-card{background:#fff5f5;border:1px solid #fecaca;border-left:4px solid #dc2626;margin:14px 0;border-radius:8px}
details.chain-card>summary{cursor:pointer;padding:12px 16px;list-style:none;transition:background .15s}
details.chain-card>summary:hover{background:#fef2f2}
details.chain-card>summary::-webkit-details-marker{display:none}
details.chain-card>summary::before{content:'▸ ';font-size:11px;color:#dc2626;font-weight:700}
details.chain-card[open]>summary::before{content:'▾ '}
details.chain-card[open]>summary{border-bottom:1px solid #fecaca}
details.chain-card>summary h3{display:inline;font-size:0.95em;margin:0;color:#991b1b}
.chain-card-body{padding:8px 16px 16px}
hr{border:none;border-top:1px solid #e2e8f0;margin:20px 0}
strong{color:#1a1a2e}
p{line-height:1.7;margin:8px 0;color:#374151}
ul,ol{margin:8px 0;padding-left:24px;line-height:1.8;color:#374151}
li{margin:2px 0}
.dashboard{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}
@media(max-width:640px){.dashboard{grid-template-columns:repeat(2,1fr)}}
.card{background:white;border-radius:12px;padding:24px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.06);border:1px solid #e2e8f0;transition:transform .15s,box-shadow .15s}
.card:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.08)}
.card .num{font-size:2.8em;font-weight:800;letter-spacing:-0.02em}
.card .label{font-size:11px;color:#64748b;margin-top:6px;text-transform:uppercase;letter-spacing:0.06em;font-weight:600}
.confirmed .num{color:#dc2626}
.confirmed{border-bottom:3px solid #dc2626}
.candidate .num{color:#ea580c}
.candidate{border-bottom:3px solid #ea580c}
.safe .num{color:#16a34a}
.safe{border-bottom:3px solid #16a34a}
.na .num{color:#94a3b8}
.na{border-bottom:3px solid #94a3b8}
.always-open{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:20px 24px;margin:14px 0;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.always-open h2{margin-top:0}
a.vuln-link{color:#1e40af;text-decoration:none;border-bottom:1px dashed #93c5fd;transition:border-color .15s,color .15s}
a.vuln-link:hover{color:#1d4ed8;border-bottom-color:#1d4ed8}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;letter-spacing:0.02em;white-space:nowrap}
.badge-confirmed{background:#fef2f2;color:#dc2626;border:1px solid #fecaca}
.badge-candidate{background:#fff7ed;color:#ea580c;border:1px solid #fed7aa}
@media print{
  body{max-width:none;padding:16px;background:white;color:black;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .dashboard{gap:8px}
  .card{box-shadow:none;border:1px solid #d1d5db;break-inside:avoid}
  details.scanner-block,details.vuln-block,details.chain-block{box-shadow:none;border:1px solid #d1d5db;break-inside:avoid}
  details>summary::before{display:none}
  pre{white-space:pre-wrap;word-wrap:break-word;border:1px solid #d1d5db}
  .report-header{background:#1e293b!important}
}
.report-header{background:linear-gradient(135deg,#1e293b 0%,#334155 100%);color:white;padding:32px;border-radius:14px;margin-bottom:24px;box-shadow:0 4px 12px rgba(0,0,0,.12)}
.report-header h1{color:white;margin:0 0 16px;font-size:1.6em}
.report-header p{color:#cbd5e1;margin:4px 0;font-size:13px;line-height:1.6}
.report-header strong{color:#f1f5f9}
.report-header code{background:rgba(255,255,255,.12);color:#e2e8f0}
'''

JS = '''
document.addEventListener('click',function(e){
  var a=e.target.closest('a[href^="#vuln-"]');
  if(!a)return;
  var vid=a.getAttribute('href').slice(1);
  var target=document.getElementById(vid);
  if(!target)return;
  var el=target;
  while(el){if(el.tagName==='DETAILS'&&!el.open)el.open=true;el=el.parentElement;}
  setTimeout(function(){target.scrollIntoView({behavior:'smooth'});},80);
});
window.addEventListener('beforeprint',function(){
  document.querySelectorAll('details:not([open])').forEach(function(d){d.open=true;d.dataset.po='1';});
});
window.addEventListener('afterprint',function(){
  document.querySelectorAll('details[data-po]').forEach(function(d){d.open=false;delete d.dataset.po;});
});
'''

out = []
out.append(f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>통합 취약점 스캔 보고서</title>
<style>{CSS}</style>
</head>
<body>
<div class="dashboard">
  <div class="card confirmed"><div class="num">{_confirmed}</div><div class="label">확인됨</div></div>
  <div class="card candidate"><div class="num">{_candidate}</div><div class="label">후보</div></div>
  <div class="card safe"><div class="num">{_safe}</div><div class="label">이상 없음</div></div>
  <div class="card na"><div class="num">{_na}</div><div class="label">미적용</div></div>
</div>''')

# 파서 상태를 딕셔너리로 관리
state = {
    'in_code': False,
    'code_lang': '',
    'code_buf': [],
    'in_table': False,
    'tbl_header': [],
    'tbl_rows': [],
    'tbl_header_done': False,
    'in_ul': False,
    'in_ol': False,
    'p_buf': [],
    'always_open_div': False,
    'scanner_results_open': False,
    'chain_open': False,
    'chain_card_open': False,
    'vuln_open': False,
    'vuln_counter': 0,
}

def do_flush_p():
    if state['p_buf']:
        out.append('<p>' + ' '.join(state['p_buf']) + '</p>')
        state['p_buf'] = []

def do_flush_list():
    if state['in_ul']:
        out.append('</ul>')
        state['in_ul'] = False
    if state['in_ol']:
        out.append('</ol>')
        state['in_ol'] = False

def split_table_cells(line):
    """백틱(인라인 코드) 내부의 | 문자를 구분자로 처리하지 않고 테이블 셀을 분리한다."""
    cells = []
    current = []
    in_backtick = False
    for ch in line:
        if ch == '`':
            in_backtick = not in_backtick
            current.append(ch)
        elif ch == '|' and not in_backtick:
            cells.append(''.join(current))
            current = []
        else:
            current.append(ch)
    if current:
        cells.append(''.join(current))
    return [c for c in cells if c != '']

def do_flush_table():
    if not state['in_table']:
        return
    out.append('<table>')
    if state['tbl_header']:
        out.append('<thead><tr>' + ''.join(f'<th>{inline(c.strip())}</th>' for c in state['tbl_header']) + '</tr></thead>')
    out.append('<tbody>')
    for row in state['tbl_rows']:
        out.append('<tr>' + ''.join(f'<td>{inline(c.strip())}</td>' for c in row) + '</tr>')
    out.append('</tbody></table>')
    state['in_table'] = False
    state['tbl_header'] = []
    state['tbl_rows'] = []
    state['tbl_header_done'] = False

def do_flush_all():
    do_flush_p()
    do_flush_list()
    do_flush_table()

def close_vuln():
    if state['vuln_open']:
        out.append('</div></details>')
        state['vuln_open'] = False

def close_chain_card():
    if state['chain_card_open']:
        out.append('</div></details>')
        state['chain_card_open'] = False

def close_chain():
    close_chain_card()
    if state['chain_open']:
        out.append('</div></details>')
        state['chain_open'] = False

def open_vuln_block(num, title):
    close_vuln()
    state['vuln_counter'] += 1
    out.append(f'<details class="vuln-block" id="vuln-{num}">')
    out.append(f'<summary><h3>{esc(title)}</h3></summary>')
    out.append('<div class="vuln-body">')
    state['vuln_open'] = True

def close_scanner_results():
    close_vuln()
    if state['scanner_results_open']:
        out.append('</div></details>')
        state['scanner_results_open'] = False

def close_always_open():
    if state['always_open_div']:
        out.append('</div>')
        state['always_open_div'] = False

for line in lines:
    # 코드 블록
    if line.startswith('```'):
        if not state['in_code']:
            do_flush_all()
            state['in_code'] = True
            state['code_lang'] = line[3:].strip()
            state['code_buf'] = []
        else:
            escaped_code = '\n'.join(esc(cl) for cl in state['code_buf'])
            lang = esc(state['code_lang']) if state['code_lang'] else ''
            out.append(f'<pre><code class="language-{lang}">{escaped_code}</code></pre>')
            state['in_code'] = False
            state['code_buf'] = []
        continue
    if state['in_code']:
        state['code_buf'].append(line)
        continue

    # **N번 ...**: 제목 / **N번 ...제목** 형식 → 취약점 블록 (서브에이전트 출력 형식 차이 흡수)
    bold_vuln_match = re.match(r'^\*\*(\d+)번[^\n*]*?[:\-]\s*(.*?)\*{0,2}\s*$', line)
    if bold_vuln_match and state['scanner_results_open'] and not state['in_code']:
        do_flush_all()
        title = bold_vuln_match.group(2).strip().rstrip('*').strip()
        if not title:
            title = re.sub(r'\*', '', line).strip()
        open_vuln_block(bold_vuln_match.group(1), title)
        continue

    # 헤딩
    h_match = re.match(r'^(#{1,4})\s+(.*)', line)
    if h_match:
        do_flush_all()
        level = len(h_match.group(1))
        title = h_match.group(2).strip()

        if level == 1:
            close_scanner_results()
            close_always_open()
            out.append(f'<h1>{esc(title)}</h1>')
            continue

        if level == 2:
            # ## N. 제목 → 스캐너별 실행 결과 내부에 있으면 취약점 블록
            num2_match = re.match(r'^(\d+)\.', title) if state['scanner_results_open'] else None
            if num2_match:
                open_vuln_block(num2_match.group(1), title)
                continue
            close_scanner_results()
            close_chain()
            close_always_open()
            if title == '스캐너별 실행 결과':
                out.append('<details class="scanner-block" open>')
                out.append('<summary><h2>스캐너별 실행 결과</h2></summary>')
                out.append('<div class="scanner-body">')
                state['scanner_results_open'] = True
            elif title == 'AI 자율 탐색 결과':
                out.append('<details class="scanner-block" open>')
                out.append('<summary><h2>AI 자율 탐색 결과</h2></summary>')
                out.append('<div class="scanner-body">')
                state['scanner_results_open'] = True
            elif title == '연계 시나리오':
                out.append('<details class="chain-block" open>')
                out.append('<summary><h2>연계 시나리오</h2></summary>')
                out.append('<div class="chain-body">')
                state['chain_open'] = True
            else:
                out.append(f'<div class="always-open"><h2>{esc(title)}</h2>')
                state['always_open_div'] = True
            continue

        if level == 3:
            # ### 체인 #N: ... → chain-card div
            if state['chain_open'] and re.match(r'^체인\s*#', title):
                do_flush_all()
                close_chain_card()
                out.append(f'<details class="chain-card"><summary><h3>{esc(title)}</h3></summary><div class="chain-card-body">')
                state['chain_card_open'] = True
                continue
            # ### [XSS] Scanner 등 스캐너 소제목
            if re.match(r'^\[', title):
                close_vuln()
                out.append(f'<h3 class="scanner-heading">{esc(title)}</h3>')
                continue
            # 스캐너 섹션 내부 + "N." 으로 시작 → 취약점 블록 (실제 번호로 id 부여)
            num3_match = re.match(r'^(\d+)\.', title) if state['scanner_results_open'] else None
            if num3_match:
                open_vuln_block(num3_match.group(1), title)
                continue
            # ### 이상없음 스캐너 이름 등 일반
            close_vuln()
            out.append(f'<h3>{esc(title)}</h3>')
            continue

        if level == 4:
            # 스캐너 섹션 내부 + "N." 으로 시작 → 취약점 블록 (실제 번호로 id 부여)
            # 숫자 없는 헤딩(원인 분석, 재현 방법 및 POC, 권장 조치 등)은 일반 h4
            num4_match = re.match(r'^(\d+)\.', title) if state['scanner_results_open'] else None
            if num4_match:
                open_vuln_block(num4_match.group(1), title)
                continue
            out.append(f'<h4>{inline(title)}</h4>')
            continue

        out.append(f'<h{level}>{inline(title)}</h{level}>')
        continue

    # 수평선
    if re.match(r'^---+$', line.strip()):
        do_flush_all()
        out.append('<hr>')
        continue

    # 빈 줄
    if line.strip() == '':
        do_flush_p()
        do_flush_list()
        do_flush_table()
        continue

    # 테이블
    if line.startswith('|'):
        cells = split_table_cells(line)
        if all(re.match(r'^[\s:-]+$', c) for c in cells):
            state['tbl_header_done'] = True
            continue
        if not state['in_table']:
            do_flush_p()
            do_flush_list()
            state['in_table'] = True
        if not state['tbl_header_done']:
            state['tbl_header'] = cells
        else:
            state['tbl_rows'].append(cells)
        continue
    else:
        do_flush_table()

    # 리스트
    ul_m = re.match(r'^(\s*)[-*]\s+(.*)', line)
    ol_m = re.match(r'^(\s*)\d+\.\s+(.*)', line)
    if ul_m:
        do_flush_p()
        if not state['in_ul']:
            do_flush_list()
            out.append('<ul>')
            state['in_ul'] = True
        out.append(f'<li>{inline(ul_m.group(2))}</li>')
        continue
    if ol_m:
        do_flush_p()
        if not state['in_ol']:
            do_flush_list()
            out.append('<ol>')
            state['in_ol'] = True
        out.append(f'<li>{inline(ol_m.group(2))}</li>')
        continue

    # 일반 텍스트
    do_flush_list()
    do_flush_table()
    # **키**: 값 형식(메타데이터 필드)은 개별 <p>로 분리
    if re.match(r'^\*\*[^*]+\*\*\s*:', line):
        do_flush_p()
    state['p_buf'].append(inline(line))

# 마무리
do_flush_all()
close_scanner_results()
close_chain()
close_always_open()

out.append(f'<script>{JS}</script>')
out.append('</body></html>')

html_out = '\n'.join(out)

# 취약점 요약 테이블 링크 추가 (총괄 요약 테이블 제외, 취약점 요약 테이블만)
# 취약점 요약 테이블: #, 취약점 제목, 유형, 스캐너, 상태 컬럼
# <tr><td>숫자</td><td>제목</td>... 패턴
def add_link(m):
    num = m.group(1)
    title_content = m.group(2)
    rest = m.group(3)
    linked = f'<a href="#vuln-{num}" class="vuln-link">{title_content}</a>'
    return f'<tr><td>{num}</td><td>{linked}</td>{rest}'

html_out = re.sub(
    r'<tr><td>(\d+)</td><td>((?:(?!</td>).)+)</td>(.*?<td>(?:확인됨|후보)</td></tr>)',
    add_link,
    html_out,
    flags=re.DOTALL
)

# 상태값을 색상 뱃지로 변환
html_out = html_out.replace('<td>확인됨</td>', '<td><span class="badge badge-confirmed">확인됨</span></td>')
html_out = html_out.replace('<td>후보</td>', '<td><span class="badge badge-candidate">후보</span></td>')

with open(_html_path, 'w', encoding='utf-8') as f:
    f.write(html_out)

poc = html_out.count('재현 방법 및 POC')
vb = html_out.count('class="vuln-block"')
print(f'POC: {poc}, vuln-block: {vb}, 파일: {len(html_out):,}bytes')
