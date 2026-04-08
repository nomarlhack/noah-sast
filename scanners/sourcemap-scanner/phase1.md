> ## 핵심 원칙: "민감한 정보가 노출되지 않으면 취약점이 아니다"
>
> Source Map 파일이 다운로드 가능하다는 것 자체가 취약점이지만, 실제 영향도는 포함된 내용에 따라 다르다. Source Map에서 API 키, 시크릿, 내부 API 경로, 주석에 포함된 자격 증명 등 민감한 정보가 발견되면 심각도가 높아진다.
>

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
