# Issue #21 Review: 로컬/배포 환경변수 기반 연결 설정 분리

## 문서 목적

이 문서는 GitHub Issue `#21 로컬/배포 환경변수 기반 연결 설정 분리`를 현재 repo 기준으로 다시 정리한 결과를 담는다.

이번 이슈의 핵심은 배포 코드를 바로 구현하는 것이 아니다.
로컬 개발 환경은 유지하면서, 배포 환경에서 달라지는 연결 설정과 환경변수 주입 방식을 먼저 고정하는 것이 목적이다.

특히 아래 질문에 대한 현재 결론과 남겨둘 검토 경계를 정리한다.

- production에서 프론트와 API를 어떤 origin과 경로로 연결할 것인가
- 로컬과 배포에서 API base URL을 어떻게 다르게 주입할 것인가
- CORS는 환경별로 어디까지 열어둘 것인가
- 인증 쿠키의 `secure` 설정은 어떻게 분리할 것인가
- `export` 직접 주입을 대체할 로컬/배포 환경변수 주입 기준은 무엇인가

## 관련 이슈

- GitHub Issue: `#21 로컬/배포 환경변수 기반 연결 설정 분리`
- 선행 문서: `docs/deployment/issue-20-deployment-auth-session-policy.md`

## 현재 구현 상태

현재 repo는 로컬 개발 환경 기준으로 프론트와 백엔드를 연결한다.

- 프론트 개발 서버는 `5173` 포트에서 실행된다.
- 백엔드는 FastAPI 서버가 `8000` 포트에서 실행된다.
- 프론트는 `VITE_API_BASE_URL`로 API 주소를 결정한다.
- 로컬 개발 기본값은 `/api`이다.
- Vite dev server가 `/api` prefix를 제거해 `http://localhost:8000` 백엔드로 프록시한다.
- 백엔드 CORS는 `localhost`, `127.0.0.1`, `5173`, `4173` 개발 서버 기준으로 열려 있다.
- 인증에 필요한 `ADMIN_PASSWORD`, `SESSION_SECRET`은 서버 시작 전 셸에서 `export`로 주입하는 흐름에 가깝다.
- 인증 쿠키는 현재 코드에서 `secure=False`로 설정되어 있다.

이 구성은 로컬 로그인/세션 검증에는 충분하다.
하지만 production 배포 기준으로는 로컬 포트와 수동 환경변수 주입 전제가 코드와 실행 절차에 남아 있다.

## 이슈가 열린 이유

로컬에서는 `5173 -> 8000` 포트 분리가 자연스럽다.
하지만 배포에서는 사용자가 접속하는 공개 URL, HTTPS, reverse proxy, 쿠키 전송 조건이 함께 맞아야 한다.

따라서 이번 이슈는 단순한 CORS 수정이 아니다.
로컬에서 우연히 맞아떨어진 연결 방식을 production에서 재현 가능한 설정 구조로 바꾸기 위한 결정 작업이다.

특히 아래 항목은 배포 전에 기준이 필요하다.

- production에서 같은 origin을 사용할지, 별도 origin을 사용할지
- 외부 API 경로를 어떻게 노출할지
- 프론트 API base URL을 코드 추론이 아니라 환경변수로 주입할지
- production에서 개발용 CORS allowlist를 계속 사용할지
- HTTP 로컬 개발과 HTTPS production에서 쿠키 `secure` 값을 어떻게 분리할지
- 수동 `export` 대신 어떤 방식으로 환경변수를 반복 주입할지

## 이번 검토에서 다시 고정한 기준

### 1. Production은 same origin 기준으로 둔다

1차 배포에서는 프론트와 API를 별도 origin으로 분리하지 않는다.
서비스는 EC2 단일 서버 안에서 프론트와 API를 함께 운영하는 방향을 기준으로 본다.

이 전제는 중요하다.

- 사용자는 하나의 공개 주소로 접속한다.
- CORS와 cross-site cookie 문제를 1차 범위에서 키우지 않는다.
- 인증 쿠키는 같은 origin 중심 흐름으로 전송된다.
- 프론트와 API의 경계는 브라우저 origin이 아니라 Nginx routing으로 나눈다.

즉 이번 이슈는 `서로 다른 origin 사이의 인증 전달` 문제가 아니라, `같은 origin 안에서 로컬/배포 설정을 어떻게 분리할 것인가`를 묻는 문제다.

### 2. Production에서는 Nginx reverse proxy를 사용한다

1차 배포에서는 S3 같은 정적 호스팅 서비스를 쓰지 않고, 같은 EC2 안에서 Nginx가 외부 공개 지점과 reverse proxy 역할을 맡는 방향을 기준으로 둔다.
다만 Nginx를 EC2 호스트에 직접 설치할지, Docker Compose 서비스로 둘지는 이번 이슈에서 확정하지 않는다.
그 배치 방식은 실제 배포 아키텍처를 구상할 때 별도로 결정한다.

이번 이슈에서 고정하는 것은 아래 범위다.

- 외부 공개 지점은 Nginx로 둔다.
- FastAPI는 외부에 직접 노출하지 않는다.
- Nginx가 프론트 정적 파일 요청과 API 요청을 구분한다.

production 외부 경로는 아래 기준으로 둔다.

- `/` 이하 기본 경로는 프론트 정적 파일로 제공한다.
- `/api/...` 요청은 FastAPI 백엔드로 프록시한다.
- Nginx는 `/api` prefix를 제거한 뒤 백엔드에 전달한다.
- FastAPI 내부 라우트는 현재처럼 `/products`, `/auth/login`, `/dashboard` 등을 유지한다.

예시는 아래와 같다.

```text
https://example.com/api/products
-> Nginx
-> http://backend:8000/products
```

`/api` prefix는 API라서 반드시 필요한 규칙이 아니다.
같은 origin 안에서 프론트 정적 파일 요청과 백엔드 API 요청을 안정적으로 구분하기 위한 운영 경계로 둔다.

### 3. 프론트 코드는 API 주소를 자동 추론하지 않는다

이전 프론트 코드는 브라우저의 현재 hostname을 읽고 `:8000`을 붙였다.
이 방식은 로컬에서는 편하지만, production 코드에 로컬 포트 전제를 남겼다.

현재 프론트 코드는 환경을 추론하지 않고 `VITE_API_BASE_URL`을 우선 사용한다.
값이 없을 때의 fallback도 `/api`로 둔다.

환경별 기준값은 아래와 같다.

```text
development:
VITE_API_BASE_URL=/api

production:
VITE_API_BASE_URL=/api
```

즉 프론트 요청 경로는 `/api`로 통일하고, 로컬에서는 Vite dev server, production에서는 Nginx가 `/api` prefix를 제거해 FastAPI 기존 라우트로 전달한다.

### 4. CORS는 환경 분리 안에서 다룬다

CORS는 이번 이슈의 독립 목표가 아니다.
프론트/API 연결 구조가 환경별로 정리되면 그에 맞춰 자연스럽게 결정되는 항목이다.

기준은 아래와 같다.

```text
development:
CORS_ALLOW_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

production:
same origin 기준이므로 개발용 CORS allowlist를 사용하지 않는다.
```

production에서 프론트와 API가 같은 origin 아래에 있으면, 브라우저 입장에서는 cross-origin 요청이 아니다.
따라서 production 기본값은 `CORS를 넓게 여는 것`이 아니라 `same origin 전제에 맞춰 최소화하는 것`으로 둔다.

추후 프론트와 API를 별도 origin으로 분리해야 할 요구가 생기면, 그때 production CORS allowlist를 다시 검토한다.

### 5. 쿠키 `secure` 설정은 환경변수로 분리한다

Issue #20에서는 production 쿠키 기준을 `HttpOnly + Secure + SameSite=Lax`로 정리했다.
하지만 현재 로컬 개발은 HTTP로 실행되므로 `secure=True`를 바로 적용하면 로컬 쿠키 전송이 깨질 수 있다.

따라서 쿠키 `secure` 여부는 환경변수로 분리한다.

```text
development:
SESSION_COOKIE_SECURE=false

production:
SESSION_COOKIE_SECURE=true
```

이 결정은 인증 방식을 바꾸는 것이 아니라, 같은 signed session cookie 방식을 환경별 실행 조건에 맞게 조정하는 것이다.

### 6. 수동 `export`는 표준 실행 방식에서 제외한다

현재처럼 새 셸마다 환경변수를 `export`로 직접 주입하는 방식은 로컬/배포의 표준 실행 방식으로 사용하지 않는다.
배포 기준은 물론이고 로컬 개발 기준에서도 반복 가능한 실행 방식이라고 보기 어렵다.

문제는 아래와 같다.

- 서버 재시작 시 환경변수 누락 위험이 있다.
- 터미널 세션에 실행 상태가 의존한다.
- 어떤 값이 production 설정인지 추적하기 어렵다.
- 반복 배포 절차로 설명하기 어렵다.

따라서 README, quickstart, 배포 문서에서 새 셸마다 `export`를 직접 입력하는 방식을 기본 실행 절차로 안내하지 않는다.

### 7. 로컬은 `.env`, production은 반복 가능한 환경변수 주입 방식을 기준으로 둔다

로컬 개발에서는 `.env` 파일을 기준으로 반복 실행 가능한 환경을 만든다.
production에서는 새 셸마다 `export`로 직접 주입하지 않고, 재시작/재배포 후에도 같은 값을 재현할 수 있는 환경변수 주입 방식을 사용한다.

현재 1차 후보는 Docker Compose의 `env_file` 또는 `environment` 설정이다.
다만 Docker Compose의 환경변수 주입 방식과 노출 범위는 아직 학습과 검토가 필요하다.
따라서 이번 이슈에서는 `수동 export를 표준 실행 방식으로 사용하지 않는다`와 `production 설정은 재현 가능한 방식으로 주입한다`까지만 고정한다.

예상 구조는 아래와 같다.

```text
local development:
.env

production:
재현 가능한 환경변수 주입 방식 사용
Docker Compose env_file 또는 environment는 1차 후보
```

Docker Compose의 `env_file`을 사용하더라도, 그것은 비밀값을 암호화하거나 보호하는 저장소가 아니다.
컨테이너 실행 시 환경변수를 재현 가능하게 주입하기 위한 수단에 가깝다.

따라서 실제 production 값은 Git에 커밋하지 않는다.
구체적인 보관 위치, 파일 권한, 서버 접근 권한, 비밀값 회전 기준은 Issue #22와 후속 배포 아키텍처 검토에서 별도로 정리한다.

## 환경변수 후보

### Backend

```text
development:
APP_ENV=development
ADMIN_PASSWORD=...
SESSION_SECRET=...
SESSION_COOKIE_SECURE=false
CORS_ALLOW_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

```text
production:
APP_ENV=production
ADMIN_PASSWORD=...
SESSION_SECRET=...
SESSION_COOKIE_SECURE=true
```

production에서는 same origin 기준이므로 개발용 CORS allowlist를 그대로 사용하지 않는다.
구체적으로 `CORS_ALLOW_ORIGINS`를 비워둘지, CORS middleware를 환경별로 조건부 적용할지는 구현 단계에서 정한다.

### Frontend

```text
VITE_API_BASE_URL=/api
```

production build에서는 아래 값을 기준으로 둔다.

```text
VITE_API_BASE_URL=/api
```

`VITE_` prefix가 붙은 값은 프론트 빌드 시점에 사용되는 값이다.
백엔드 런타임 환경변수와 다르게 취급해야 한다.

## 결론

### 1. #21은 설정 주입 구조를 정리하는 이슈다

이번 이슈는 인증 방식이나 배포 구조 전체를 바꾸는 작업이 아니다.
로컬과 production에서 달라지는 설정을 코드가 아니라 환경변수로 분리하는 것이 핵심이다.

### 2. Production은 `same origin + /api reverse proxy` 기준으로 둔다

Nginx를 외부 공개 지점으로 두고 프론트 정적 파일과 API 요청을 나눈다.
외부 API는 `/api/...`로 노출하고, 내부 FastAPI 라우트는 기존 경로를 유지한다.
Nginx의 실제 배치 방식은 후속 배포 아키텍처에서 확정한다.

### 3. 코드는 환경을 추론하지 않고 환경변수 값을 따른다

프론트는 `VITE_API_BASE_URL`만 사용한다.
백엔드는 `CORS_ALLOW_ORIGINS`, `SESSION_COOKIE_SECURE` 같은 환경변수로 개발/배포 차이를 나눈다.

### 4. 수동 `export`는 표준 실행 방식에서 제외한다

로컬은 `.env`, production은 수동 `export`가 아닌 반복 가능한 환경변수 주입 방식을 기준으로 둔다.
실제 비밀값은 Git에 커밋하지 않고, production secret 운영 기준은 Issue #22에서 별도로 다룬다.

## 이번 결정으로 정리되는 규칙

- 1차 배포는 EC2 단일 서버 안에서 프론트와 API를 함께 운영하는 방향으로 본다.
- production은 same origin 구조를 기본값으로 둔다.
- Nginx는 외부 공개 지점과 reverse proxy 역할을 맡는다.
- Nginx를 호스트에 직접 둘지 Docker Compose 서비스로 둘지는 후속 배포 아키텍처에서 확정한다.
- FastAPI는 외부에 직접 노출하지 않는다.
- production 외부 API namespace는 `/api`로 둔다.
- Nginx는 `/api` prefix를 제거한 뒤 FastAPI에 전달한다.
- FastAPI 내부 라우트는 현재 경로를 유지한다.
- 프론트 API 주소는 `VITE_API_BASE_URL` 환경변수로만 결정한다.
- development의 `VITE_API_BASE_URL`은 `/api`로 둔다.
- development에서는 Vite dev server가 `/api` prefix를 제거해 `http://localhost:8000` 백엔드로 프록시한다.
- production의 `VITE_API_BASE_URL`은 `/api`로 둔다.
- 현재 MVP의 공식 프론트 화면 URL은 `/` 하나로 둔다.
- fallback으로 열린 정의되지 않은 프론트 경로는 앱 부팅 시 `/`로 정규화한다.
- SPA fallback과 routing 정책은 `docs/deployment/issue-28-spa-fallback-routing-policy.md`에서 다룬다.
- development CORS allowlist는 로컬 프론트 개발 서버 origin을 허용한다.
- production에서는 same origin 기준으로 개발용 CORS allowlist를 사용하지 않는다.
- development의 `SESSION_COOKIE_SECURE`는 `false`로 둔다.
- production의 `SESSION_COOKIE_SECURE`는 `true`로 둔다.
- 수동 `export`는 로컬/배포 표준 실행 방식으로 사용하지 않는다.
- 로컬은 `.env`를 기준으로 둔다.
- production은 수동 `export`가 아니라 반복 가능한 환경변수 주입 방식을 사용한다.
- Docker Compose의 `env_file` 또는 `environment` 설정은 production 환경변수 주입의 1차 후보로 둔다.
- 구체적인 Docker Compose 주입 방식은 학습과 배포 아키텍처 검토 후 확정한다.
- 실제 production 비밀값은 Git에 커밋하지 않는다.

## 반영 상태와 다음 후보

- 반영됨: 프론트 API base URL을 `VITE_API_BASE_URL` 기준으로 변경하기
- 반영됨: 로컬 `frontend/.env.example` 작성하기
- 백엔드 CORS allowlist를 환경변수 기반으로 변경하기
- 쿠키 `secure` 설정을 `SESSION_COOKIE_SECURE` 기준으로 변경하기
- production 환경변수 주입 예시와 Git 제외 규칙 정리하기
- Docker Compose env 주입 방식 학습 및 배포 설정에 반영하기
