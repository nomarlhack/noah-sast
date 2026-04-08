> ## 핵심 원칙: "CSS가 조작되지 않으면 취약점이 아니다"
>
> 소스코드에서 사용자 입력이 style 속성에 반영된다고 바로 취약점으로 보고하지 않는다. 실제로 CSS 구문을 삽입하여 의도하지 않은 스타일이 적용되거나, CSS 기반 데이터 탈취가 가능한 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

사용자 입력 → CSS 삽입 경로를 추적하여 취약점 **후보**를 식별한다.

1. **프로젝트 스택 파악**: 프레임워크/템플릿 엔진/CSS 처리 방식 확인

2. **Source 식별**: 사용자가 제어 가능한 입력 중 CSS에 반영될 수 있는 것
   - 테마/색상 커스터마이징 기능 (사용자 지정 색상, 배경 등)
   - 프로필 설정 (배경색, 글꼴, 스타일)
   - URL 파라미터가 인라인 스타일에 반영되는 경우
   - 사용자 입력이 CSS 클래스명에 반영되는 경우
   - CMS에서 사용자가 CSS를 직접 입력할 수 있는 기능
   - 이메일 HTML 템플릿에서 사용자 입력이 스타일에 반영되는 경우

3. **Sink 식별**: 사용자 입력이 CSS로 출력되는 코드

   **인라인 스타일 삽입:**
   ```html
   <!-- React — 위험: 사용자 입력이 style 객체에 직접 삽입 -->
   <div style={{ color: userInput }}>

   <!-- HTML — 위험: 사용자 입력이 style 속성에 삽입 -->
   <div style="color: ${userInput}">

   <!-- 위험: background-image에 사용자 URL 삽입 -->
   <div style="background-image: url(${userInput})">
   ```

   **`<style>` 태그 내 삽입:**
   ```html
   <style>
     .user-theme { color: ${userInput}; }
   </style>
   ```

   **CSS 파일 동적 생성:**
   ```javascript
   // 위험: 사용자 입력으로 CSS 생성
   const css = `.profile { background-color: ${userColor}; }`;
   ```

   **CSS-in-JS:**
   ```javascript
   // React styled-components — 위험: 사용자 입력이 CSS 값에 직접 삽입
   const StyledDiv = styled.div`
     color: ${props => props.userColor};
   `;
   ```

   **안전한 패턴:**
   ```javascript
   // 안전: 허용된 값만 선택 (화이트리스트)
   const color = allowedColors.includes(userInput) ? userInput : 'black';

   // 안전: CSS 변수를 통한 값 전달 (속성값만 변경, 구문 삽입 불가)
   element.style.setProperty('--user-color', sanitizedValue);

   // 안전: React의 style 객체에서 값만 전달 (키는 고정)
   <div style={{ color: sanitizedColor }}> // 단, sanitizedColor에 ; } 등이 없어야 함
   ```

4. **경로 추적**: Source에서 Sink까지 데이터 흐름 확인
   - CSS 값에 `;`, `}`, `{`, `url(`, `@import`, `expression(` 등 CSS 메타문자가 삽입 가능한지
   - CSS sanitization 라이브러리 사용 여부 (`DOMPurify`의 CSS 모드, `css.escape()` 등)
   - Content Security Policy (CSP)의 `style-src` 설정 — `unsafe-inline` 허용 여부
   - React의 `style` prop은 객체이므로 CSS 구문 삽입이 제한적이지만, 값에 `url()` 삽입은 가능

5. **후보 목록 작성**: 각 후보에 대해 "어떤 입력으로 어떻게 CSS를 조작할 수 있는지"를 구체적으로 구상. 데이터 흐름 추적을 완료한 뒤에도 공격 경로가 없으면 버린다. 추적 없이 직관으로 버리지 않는다..

## 후보 판정 제한

사용자 입력이 CSS 속성값에 삽입되는 경우만 후보.
