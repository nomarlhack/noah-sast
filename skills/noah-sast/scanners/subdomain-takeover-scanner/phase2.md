### Phase 2: 동적 테스트 (검증)

Phase 1 분석이 완료되면 후보 목록을 사용자에게 보여준다. 후보가 존재하는 경우에만 동적 테스트를 진행한다. 후보가 0건이면 동적 테스트 없이 바로 보고서를 작성한다.

**동적 테스트 정보 획득:**

사용자에게는 테스트 대상 도메인(Host)과 직접 획득이 불가능한 정보(외부 콜백 서비스 URL, 프로덕션 전용 자격 증명 등)만 요청한다. 그 외의 정보는 소스코드 분석 또는 관련 엔드포인트에 직접 HTTP 요청을 보내 획득한다.

사용자가 동적 테스트를 원하지 않거나 정보를 제공하지 않으면, 소스코드 분석 결과의 모든 후보를 "후보"로 유지한 채 Phase 3으로 진행한다.

**Step 1: DNS CNAME 확인**
```
# 서브도메인의 CNAME 레코드 확인
dig CNAME blog.target.com +short
# target.github.io. → GitHub Pages를 가리킴

# 또는
nslookup -type=CNAME blog.target.com

# 여러 서브도메인 일괄 확인
for sub in blog docs api staging; do
  echo -n "$sub.target.com → "
  dig CNAME "$sub.target.com" +short
done
```

**Step 2: 서비스 응답 확인**
```
# HTTP 응답 확인 — 미사용 서비스의 특징적 에러 메시지 확인
curl -sI "https://blog.target.com" | head -20
curl -s "https://blog.target.com" | head -50

# GitHub Pages 미사용
# → "There isn't a GitHub Pages site here"

# S3 버킷 미존재
# → "<Code>NoSuchBucket</Code>"

# Heroku 미사용
# → "No such app"
```

**Step 3: 서비스별 상세 확인**
```
# S3 버킷 존재 여부 확인
curl -s "http://BUCKET_NAME.s3.amazonaws.com/" | grep "NoSuchBucket"

# GitHub Pages 확인
curl -s "https://SUBDOMAIN" | grep "There isn't a GitHub Pages site here"

# Azure 확인
dig A SUBDOMAIN +short
# NXDOMAIN이면 잠재적 takeover 가능
```

**검증 기준:**
- **확인됨**: CNAME이 외부 서비스를 가리키고, 해당 서비스에서 미사용 에러 응답(NoSuchBucket, "No such app" 등)이 반환되어 공격자가 리소스를 생성할 수 있음이 확인됨
- **후보**: CNAME이 외부 서비스를 가리키지만 서비스 상태를 동적으로 확인하지 못한 경우, 또는 DNS 조회 결과가 모호한 경우
- **"확인됨"은 동적 테스트를 통해서만 부여할 수 있다**: 소스코드 분석만으로는 아무리 취약해 보여도 "확인됨"으로 보고하지 않는다. 동적 테스트로 실제 트리거를 확인한 경우에만 "확인됨"이다. 동적 테스트를 수행하지 않았으면 모든 결과는 "후보"이다.
- **보고서 제외**: CNAME이 정상 서비스를 가리키고 해당 서비스가 활성 상태인 경우
