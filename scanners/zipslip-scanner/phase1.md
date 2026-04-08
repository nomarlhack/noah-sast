> ## 핵심 원칙: "의도하지 않은 경로에 파일이 생성되지 않으면 취약점이 아니다"
>
> 소스코드에서 압축 해제 기능이 있다고 바로 취약점으로 보고하지 않는다. 실제로 `../../../etc/cron.d/malicious` 같은 경로를 가진 엔트리가 포함된 악성 압축 파일을 업로드하여 대상 디렉토리 밖에 파일이 생성되는 것을 확인해야 취약점이다.
>

### Phase 1: 정찰 (소스코드 분석)

압축 해제 로직을 분석하여 경로 검증 미흡을 식별한다.

1. **프로젝트 스택 파악**: 압축 처리 라이브러리 확인

   **Node.js:**
   - `adm-zip` — `extractAllTo()`, `extractEntryTo()`: 기본적으로 경로 검증 없음 (v0.5.10+ 패치)
   - `unzipper` / `unzip-stream` — 스트리밍 해제, 경로 검증 필요
   - `yauzl` — 안전한 API 설계 (엔트리 이름만 반환, 직접 해제하지 않음)
   - `tar` / `tar-stream` — TAR 해제
   - `archiver` — 압축 생성 (해제 아님, 안전)
   - `decompress` — 다양한 포맷 지원

   **Python:**
   - `zipfile.extractall()` — Python 3.12+ 기본 방어 (`data_filter`), 이전 버전 취약
   - `zipfile.extract()` — 경로 검증 없음
   - `tarfile.extractall()` — Python 3.12+ 기본 방어, 이전 버전 `..` 경로 허용
   - `shutil.unpack_archive()` — 내부적으로 zipfile/tarfile 사용

   **Java:**
   - `java.util.zip.ZipInputStream` — 엔트리 이름에 대한 검증이 개발자 책임
   - `java.util.zip.ZipFile` — 동일
   - `java.util.jar.JarInputStream` — ZIP과 동일 구조
   - Apache Commons Compress — `ZipArchiveInputStream`, `TarArchiveInputStream`

   **Ruby:**
   - `rubyzip` (`Zip::File`) — v1.3.0+ 기본 방어
   - `minitar` — TAR 해제

   **PHP:**
   - `ZipArchive::extractTo()` — 경로 검증 없음
   - `PharData::extractTo()` — TAR/PHAR 해제

   **Go:**
   - `archive/zip` — 엔트리 이름 검증이 개발자 책임
   - `archive/tar` — 동일

2. **Source 식별**: 사용자가 압축 파일을 제공할 수 있는 경로
   - 파일 업로드 기능 (ZIP, TAR, JAR, WAR 업로드)
   - 패키지/플러그인/테마 설치 기능
   - 데이터 임포트 기능 (CSV ZIP, 백업 파일 등)
   - CI/CD 아티팩트 배포
   - 이메일 첨부 파일 처리

3. **Sink 식별**: 압축 해제를 수행하는 코드

   **취약한 패턴:**
   ```javascript
   // Node.js adm-zip — 경로 검증 없이 해제
   const zip = new AdmZip(uploadedFile);
   zip.extractAllTo(targetDir, true);
   ```

   ```python
   # Python — 경로 검증 없이 해제
   with zipfile.ZipFile(uploaded_file) as zf:
       zf.extractall(target_dir)
   ```

   ```java
   // Java — 엔트리 이름을 그대로 경로에 사용
   ZipEntry entry = zis.getNextEntry();
   File file = new File(targetDir, entry.getName());
   // entry.getName()이 "../../../evil.sh"이면 targetDir 밖에 생성
   ```

   ```php
   // PHP — 경로 검증 없이 해제
   $zip = new ZipArchive();
   $zip->open($uploadedFile);
   $zip->extractTo($targetDir);
   ```

   **안전한 패턴:**
   ```java
   // Java — 정규화된 경로가 대상 디렉토리 안에 있는지 검증
   ZipEntry entry = zis.getNextEntry();
   File file = new File(targetDir, entry.getName());
   String canonicalPath = file.getCanonicalPath();
   String canonicalTarget = targetDir.getCanonicalPath() + File.separator;
   if (!canonicalPath.startsWith(canonicalTarget)) {
       throw new SecurityException("Zip Slip detected: " + entry.getName());
   }
   ```

   ```python
   # Python 3.12+ — data_filter로 안전한 해제
   with zipfile.ZipFile(uploaded_file) as zf:
       zf.extractall(target_dir, filter='data')
   ```

4. **경로 추적**: Source에서 Sink까지 데이터 흐름 확인
   - 엔트리 이름에 `../` 포함 여부 검증 로직
   - 정규화된 경로(canonical path)와 대상 디렉토리 비교 로직
   - 라이브러리 버전 확인 (패치된 버전인지)
   - `extractAll` 같은 편의 함수의 내부 경로 검증 여부

5. **후보 목록 작성**: 각 후보에 대해 "어떤 악성 압축 파일로 어떤 경로에 파일을 생성할 수 있는지"를 구체적으로 구상.

## 후보 판정 제한

사용자 업로드 파일을 압축 해제하는 코드가 있는 경우만 후보.
