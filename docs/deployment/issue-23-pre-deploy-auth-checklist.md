# Issue #23 Review: 배포 전 인증 검증 체크리스트 정리

## 문서 목적

이 문서는 GitHub Issue `#23 배포 전 인증 검증 체크리스트 정리`를 현재 repo 기준으로 다시 정리한 결과를 담는다.

이번 이슈의 핵심은 새 인증 기능을 추가하거나 배포 설정을 구현하는 것이 아니다.
Issue #21과 Issue #22에서 정한 production 기준을 실제 배포 URL에서 반복 확인할 수 있도록, 배포 전 인증 검증 항목과 순서를 정리하는 것이 목적이다.

특히 아래 질문에 대한 체크리스트 기준을 남긴다.

- 로그인 / 로그아웃 / 세션 유지가 실제 배포 URL에서 동작하는가
- 비로그인 상태에서 보호 API가 차단되는가
- 세션 만료와 쿠키 위변조가 안전하게 거부되는가
- production `VITE_API_BASE_URL=/api` 기준이 빌드에 반영되었는가
- Nginx가 `/api` prefix를 제거해 FastAPI 기존 라우트로 전달하는가
- FastAPI가 외부에 직접 노출되지 않는가
- production 공개 범위와 CORS, 쿠키 설정이 기존 결정과 맞는가

## 이슈가 열린 이유

현재 접근 제어 1차 구현은 로컬에서 아래 동작을 확인했다.

- 로그인 / 로그아웃
- 세션 쿠키 발급
- 비로그인 상태 보호 API 차단
- 쿠키 위변조 차단
- 세션 만료 후 로그인 화면 복귀

하지만 로컬 검증과 production 배포 검증은 다르다.
배포 URL, HTTPS, reverse proxy, 쿠키 `Secure`, CORS, 공개 엔드포인트, production 환경변수 주입이 함께 맞아야 한다.

따라서 이번 이슈는 로컬에서 이미 확인한 인증 동작을 production 배포 조건에서 다시 확인할 수 있게 만드는 후속 검증 단계다.

## 선행 기준

Issue #23은 새 정책을 정하지 않는다.
검증 기준은 Issue #21과 Issue #22에서 정한 내용을 따른다.

### Issue #21 기준

- 1차 배포는 EC2 단일 서버 안에서 프론트와 API를 함께 운영하는 방향으로 본다.
- production은 `same origin + /api reverse proxy` 기준으로 둔다.
- production의 `VITE_API_BASE_URL`은 `/api`로 둔다.
- Nginx는 `/api` prefix를 제거한 뒤 FastAPI 기존 라우트로 전달한다.
- FastAPI는 외부에 직접 노출하지 않는다.
- production에서는 same origin 기준으로 개발용 CORS allowlist를 그대로 사용하지 않는다.
- production의 `SESSION_COOKIE_SECURE`는 `true`로 둔다.
- production의 `API_DOCS_ENABLED`는 `false`로 둔다.

### Issue #22 기준

- production 공개 엔드포인트는 `GET /health`만 둔다.
- production에서 `/docs`, `/openapi.json`, `/redoc`은 닫는다.
- `GET /health` 응답에는 내부 설정, DB 경로, secret, 상세 인프라 정보를 넣지 않는다.
- production secret은 `ADMIN_PASSWORD`, `SESSION_SECRET`으로 둔다.
- secret은 Git, 문서, 로그에 원문으로 남기지 않는다.
- `SESSION_SECRET` 변경은 기존 세션 전체 무효화로 취급한다.

## 배포 전 검증 항목

### 1. Production 설정 주입

- production 빌드에서 `VITE_API_BASE_URL=/api`가 반영되는지 확인한다.
- production에서 `SESSION_COOKIE_SECURE=true`가 적용되는지 확인한다.
- production에서 `API_DOCS_ENABLED=false`가 적용되는지 확인한다.
- `ADMIN_PASSWORD`, `SESSION_SECRET`이 누락되지 않았는지 확인한다.
- secret 원문이 Git, 문서, 로그에 남지 않는지 확인한다.
- production 환경변수 주입이 수동 `export`에 의존하지 않는지 확인한다.

### 2. 공개 범위

- `GET /health`가 인증 없이 접근 가능한지 확인한다.
- `GET /health` 응답에 내부 설정, DB 경로, secret, 상세 인프라 정보가 없는지 확인한다.
- production에서 `/docs`가 공개되지 않는지 확인한다.
- production에서 `/openapi.json`이 공개되지 않는지 확인한다.
- `GET /health` 외 운영 API가 인증 없이 열려 있지 않은지 확인한다.

### 3. Reverse proxy와 API 경로

- 외부 API 경로가 `/api/...` namespace를 사용하는지 확인한다.
- Nginx가 `/api` prefix를 제거한 뒤 FastAPI 기존 라우트로 전달하는지 확인한다.
- FastAPI가 외부에 직접 노출되지 않는지 확인한다.
- 브라우저 네트워크 탭에서 프론트 요청이 배포 URL 기준 `/api/...`로 나가는지 확인한다.

### 4. 로그인과 세션

- 배포 URL 접속 시 비로그인 사용자가 로그인 화면으로 진입하는지 확인한다.
- 올바른 운영자 비밀번호로 로그인되는지 확인한다.
- 로그인 후 새로고침해도 세션이 유지되는지 확인한다.
- 로그아웃 후 세션이 해제되고 보호 화면 접근이 차단되는지 확인한다.
- 세션 만료 후 보호 화면 접근 시 로그인 화면으로 돌아가는지 확인한다.

### 5. 보호 API 차단

- 비로그인 상태에서 보호 API 요청이 401로 거부되는지 확인한다.
- 로그인 상태에서 보호 API 요청이 정상 처리되는지 확인한다.
- 로그아웃 후 같은 보호 API 요청이 다시 401로 거부되는지 확인한다.

### 6. 쿠키 보안 조건

- 세션 쿠키 이름이 `store_expiration_session`인지 확인한다.
- 쿠키에 `HttpOnly`가 적용되는지 확인한다.
- HTTPS production에서 쿠키에 `Secure`가 적용되는지 확인한다.
- 쿠키 `SameSite`가 `Lax` 기준인지 확인한다.
- 쿠키 값을 임의로 바꾸면 세션이 거부되는지 확인한다.

### 7. CORS

- production에서 개발용 `localhost`, `127.0.0.1`, `5173`, `4173` allowlist를 그대로 사용하지 않는지 확인한다.
- 배포 URL 기준 same origin 요청으로 동작하는지 확인한다.
- 로그인 후 API 요청에 세션 쿠키가 포함되는지 확인한다.

## Runbook으로 옮긴 실행 절차

위 검증 항목은 실제 배포 때 기록 가능한 순서로 실행해야 한다.
따라서 실행 절차와 결과 기록 칸은 별도 Runbook 초안에 둔다.

```text
docs/deployment/pre-deploy-auth-runbook.md
```

Runbook은 아래 역할을 가진다.

- 배포 직전 확인할 설정 항목을 제공한다.
- `curl`로 확인할 공개 경로와 보호 API 항목을 제공한다.
- 브라우저에서 확인할 로그인, 세션, 쿠키 항목을 제공한다.
- 실패 항목을 후속 이슈로 넘길 수 있게 기록 양식을 제공한다.

README에는 `배포 전 확인` 섹션을 두어 Runbook 진입점을 노출한다.
나중에 실제 1차 배포 이슈를 진행할 때도 첫 체크박스에서 이 Runbook을 확인한다.

## 이번 이슈에서 바로 하지 않을 것

- 인증 구현 방식 변경
- 환경변수 주입 구조 구현
- CORS / API 주소 설정 자체 수정
- Nginx 배치 방식 결정
- Docker Compose 환경변수 주입 방식 결정
- 공개 범위 정책 새로 결정
- production `/docs`, `/openapi.json` 비활성화 구현
- 쿠키 `secure` 설정 코드 변경
- 실제 EC2 배포 수행
- staging 환경 추가
- 서버 저장 세션 전환
- 공개 회원가입 추가
- 운영 통계 기능 추가

## 이번 결정으로 정리되는 규칙

- Issue #23은 Issue #21, Issue #22에서 정한 기준을 실제 배포 URL에서 확인하는 후속 검증 이슈다.
- 체크리스트는 production 설정, 공개 범위, reverse proxy, 로그인/세션, 보호 API, 쿠키, CORS 검증을 포함한다.
- 실행 순서와 결과 기록 칸은 `docs/deployment/pre-deploy-auth-runbook.md`에 둔다.
- `docs/deployment/issue-23-pre-deploy-auth-checklist.md`는 검증 기준과 범위를 정리하는 결정 문서로 둔다.
- README에는 배포 전 확인 진입점을 둔다.
- 체크리스트 실패 항목은 그 자리에서 임의 수정하지 않고, 배포 작업 또는 후속 이슈로 책임을 분리한다.
- 이번 이슈는 검증 절차를 정리하는 문서 작업이며, production 설정 구현은 Issue #33 같은 후속 설정 작업에서 다룬다.

## 다음 반영 후보

- 실제 1차 배포 이슈에서 Runbook을 기준으로 검증 기록 남기기
- Docker Compose 기반 1차 배포 Runbook 작성하기
- production 환경변수 주입 방식 결정하기
- Issue #33에서 반영한 `SESSION_COOKIE_SECURE`, `API_DOCS_ENABLED`, CORS 설정을 실제 배포 환경에서 검증하기
