> **호출부 추적 — 실제 URL 경로 확정**: 모든 후보에 대해 라우트 정의 파일을 Read로 읽어 실제 URL 경로를 확정한다. 컴포넌트/파일 이름에서 경로를 유추하는 것은 확정이 아니다. 절차: (1) Sink의 호출부를 Grep → 최종 페이지 컴포넌트/컨트롤러 식별 (2) 라우트 정의(routes/index.tsx, @RequestMapping 등)를 Read로 읽어 경로 문자열 확인 (3) 후보 반환 시 근거 포함: `실제 경로: /home/apply (src/routes/index.tsx:42)`

### Phase 1: Source Map 탐지

1. **소스코드/빌드 설정 분석**: Source Map 생성 설정 확인

   **Webpack:**
   - `devtool` 설정: `source-map`, `hidden-source-map`, `nosources-source-map` 등
   - `source-map`이면 .map 파일 생성 + JS 파일에 `//# sourceMappingURL` 주석 포함
   - `hidden-source-map`이면 .map 파일 생성하지만 `sourceMappingURL` 주석 미포함
   - 프로덕션 빌드에서 `devtool: false` 또는 미설정인지 확인

   **Vite:**
   - `build.sourcemap` 설정: `true`, `false`, `'hidden'`, `'inline'`

   **Next.js:**
   - `next.config.js`의 `productionBrowserSourceMaps` 설정

   **Create React App:**
   - `GENERATE_SOURCEMAP=false` 환경변수

   **Vue CLI:**
   - `vue.config.js`의 `productionSourceMap` 설정

2. **배포된 JS/CSS 파일에서 sourceMappingURL 확인**:
   소스코드에서 빌드 설정을 확인한 뒤, 동적 테스트로 실제 배포 파일을 확인한다.
