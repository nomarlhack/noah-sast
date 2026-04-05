---
grep_patterns:
  - "\\.github\\.io"
  - "\\.s3\\.amazonaws\\.com"
  - "\\.s3-website"
  - "\\.herokuapp\\.com"
  - "\\.herokudns\\.com"
  - "\\.azurewebsites\\.net"
  - "\\.cloudapp\\.azure\\.com"
  - "\\.blob\\.core\\.windows\\.net"
  - "\\.cloudfront\\.net"
  - "aws_route53_record"
  - "cloudflare_record"
  - "CNAME"
  - "github\\.io"
---

# Subdomain Takeover Scanner

소스코드/설정에서 외부 서비스를 가리키는 DNS 레코드와 서비스 설정을 분석한 뒤, 동적 테스트로 실제로 해당 서브도메인이 미사용 상태여서 공격자가 장악할 수 있는지 검증하여 확인된 취약점만 보고하는 스킬이다.

## 핵심 원칙: "공격자가 서브도메인을 장악할 수 없으면 취약점이 아니다"

DNS CNAME 레코드가 외부 서비스를 가리킨다고 바로 취약점으로 보고하지 않는다. 해당 외부 서비스에서 리소스가 해제/삭제되어 있고, 공격자가 같은 이름으로 리소스를 생성하여 서브도메인 콘텐츠를 제어할 수 있는 것을 확인해야 취약점이다.

## Subdomain Takeover의 원리

1. `blog.target.com`이 CNAME으로 `target.github.io`를 가리킴
2. GitHub Pages에서 해당 리포지토리/사이트가 삭제됨
3. DNS CNAME은 여전히 `target.github.io`를 가리킴 (Dangling DNS)
4. 공격자가 GitHub에서 `target.github.io`를 생성하고 `blog.target.com`을 커스텀 도메인으로 설정
5. `blog.target.com`이 공격자의 콘텐츠를 서빙

## 취약한 외부 서비스 목록

| 서비스 | CNAME 패턴 | 미사용 시 응답 |
|--------|-----------|---------------|
| GitHub Pages | `*.github.io` | 404 "There isn't a GitHub Pages site here" |
| AWS S3 | `*.s3.amazonaws.com`, `*.s3-website-*.amazonaws.com` | 404 "NoSuchBucket" |
| AWS CloudFront | `*.cloudfront.net` | "Bad Request" / "The request could not be satisfied" |
| Heroku | `*.herokuapp.com`, `*.herokudns.com` | "No such app" |
| Azure | `*.azurewebsites.net`, `*.cloudapp.azure.com`, `*.blob.core.windows.net` | NXDOMAIN 또는 기본 Azure 페이지 |
| Shopify | `*.myshopify.com` | "Sorry, this shop is currently unavailable" |
| Tumblr | `*.tumblr.com` | "There's nothing here" / "Whatever you were looking for doesn't currently exist" |
| WordPress.com | `*.wordpress.com` | "Do you want to register" |
| Fastly | `*.fastly.net` | "Fastly error: unknown domain" |
| Pantheon | `*.pantheonsite.io` | 404 "The gods are angry" |
| Zendesk | `*.zendesk.com` | "Help Center Closed" |
| Unbounce | `*.unbouncepages.com` | "The requested URL was not found" |
| Surge.sh | `*.surge.sh` | "project not found" |
| Netlify | `*.netlify.app` | "Not Found" (단, Netlify는 기본적으로 방어됨) |
| Vercel | `*.vercel.app` | 보통 방어됨 (도메인 소유권 검증) |

## 분석 프로세스

이 스캐너의 분석은 두 단계로 구성된다:

1. **Phase 1 (소스코드 분석)**: `phase1.md` 참조
2. **Phase 2 (동적 테스트)**: `phase2.md` 참조

