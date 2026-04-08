### Phase 2: 동적 테스트 (검증)


**테스트 방법:**
1. 수학 연산 페이로드로 템플릿 엔진 실행 확인
2. 응답에서 연산 결과가 반환되는지 확인

**범용 탐지 페이로드 (엔진 식별용):**
- `{{7*7}}` → `49`이면 Jinja2/Twig/Nunjucks 계열
- `${7*7}` → `49`이면 Mako/Thymeleaf/Freemarker 계열
- `<%= 7*7 %>` → `49`이면 EJS/ERB 계열
- `#{7*7}` → `49`이면 Pug/Jade 계열
- `{{7*'7'}}` → `7777777`이면 Jinja2 (문자열 반복), `49`이면 Twig

**curl 예시:**
```
# Jinja2/Twig/Nunjucks 테스트
curl "https://target.com/search?q=%7B%7B7*7%7D%7D"

# EJS/ERB 테스트
curl "https://target.com/search?q=%3C%25%3D+7*7+%25%3E"

# Mako/Thymeleaf 테스트
curl "https://target.com/search?q=%24%7B7*7%7D"
```

**검증 기준:**
- **확인됨**: 동적 테스트로 응답에서 수학 연산 결과(`49`)가 반환된 것을 직접 확인함
