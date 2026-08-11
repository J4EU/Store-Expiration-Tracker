# Issue #41 Review: 로컬 최소 배포 경로 구성 및 검증

## 문서 목적

이 문서는 GitHub Issue `#41 로컬 최소 배포 경로 구성 및 검증`의 구조, 구현 범위, 로컬 검증 결과를 한곳에 남긴다.

> 실제 운영 배포로 옮길 수 있는 최소 요청 경로를 로컬에서 구성하고, 의도한 연결·공개·저장 경계가 실제로 동작하는지 검증한다.

따라서 구조 결정, Dockerfile·Compose·proxy 구현, 로컬 실행, 관찰 결과에 따른 보정은 하나의 작업 사이클로 다룬다.

## 배경

현재 로컬 개발은 Vite dev server와 FastAPI를 각각 실행하며, Vite가 `/api` 요청을 FastAPI로 프록시한다.

이 개발 흐름만으로는 실제 운영 전환 전에 필요한 다음 경계를 함께 확인하기 어렵다.

- 사용자가 접속하는 단일 외부 진입점
- frontend 정적 파일과 API 요청의 분기
- `/api` 요청이 FastAPI 기존 라우트로 전달되는 규칙
- backend를 호스트에 직접 공개하지 않는 연결 방식
- SQLite 데이터를 컨테이너 생명주기와 분리하는 방법

## 목표와 범위

이번 이슈에서는 아래 순서를 한 번의 피드백 루프로 수행한다.

```text
최소 구조 결정
  -> Dockerfile · Compose · proxy 구성
  -> 로컬 기동
  -> 요청 · 공개 · 저장 경계 검증
  -> 관찰 결과 반영
  -> 실제 운영 전환에 필요한 다음 작업 식별
```

Docker Compose와 Nginx는 현재 이 구조를 구현하는 수단이다.

## 최소 배포 구조

이번 로컬 검증 구조는 아래와 같다.

```text
browser
  -> http://localhost:8080 (Nginx만 호스트 포트 공개)
      -> /            : frontend 정적 파일
      -> /api/...     : /api prefix 제거
                         -> backend:8000 (Compose 내부 통신)
                             -> /app/data/store_expiration_tracker.db
                                (sqlite_data named volume)
```

요청 URL은 아래 두 경계로 나뉜다.

```text
browser -> http://localhost:8080

/ 또는 /dashboard
  -> Nginx의 정적 파일·SPA fallback
  -> index.html
  -> Vue 앱 실행
  -> 공식 화면 URL은 /로 정규화

/api
  -> 308 Location: /api/

/api/...
  -> Nginx reverse proxy
  -> /api prefix 제거
  -> backend:8000의 기존 FastAPI route
```

각 구성 요소의 책임은 다음과 같다.

| 구성 요소 | 책임 |
| --- | --- |
| Nginx | 단일 외부 진입점, frontend 정적 파일 제공, `/api/...` 요청 전달 |
| backend | FastAPI 기존 라우트 처리, SQLite 접근 |
| Docker Compose | 서비스 기동 순서·내부 네트워크·환경변수·volume 연결 |
| sqlite_data | backend 컨테이너 재생성·중지와 DB 파일을 분리하는 로컬 저장 경계 |

Nginx는 `/api` prefix를 제거해 backend의 기존 `/health`, `/auth/login`, `/auth/session` 등으로 전달한다. backend에는 `ports`를 두지 않고, Compose 내부의 `backend:8000`으로만 연결한다.

## 구현 결과

- backend와 frontend 각각의 production 이미지를 구성했다.
- Compose는 Nginx의 `8080:80`만 호스트에 공개하고, backend에는 `ports`를 두지 않는다. 동일 Compose 기본 네트워크에서 Nginx가 `backend:8000`으로 연결한다.
- `sqlite_data` named volume을 backend의 `/app/data`에 마운트했다.
- `deploy/compose-local/backend.env.example` 예시를 두고, 실제 `deploy/compose-local/backend.env`는 `.gitignore`와 `.dockerignore`에 명시해 Git과 backend Docker build context에서 제외했다.
- `/api`는 `/api/`로 정규화하고, `/api/...`는 prefix를 제거한 뒤 backend에 전달한다.

## 로컬 검증 결과

### 로컬 Compose 환경변수 준비

```bash
cp deploy/compose-local/backend.env.example deploy/compose-local/backend.env
```

`deploy/compose-local/backend.env`에는 로컬 전용 `ADMIN_PASSWORD`와 `SESSION_SECRET`을 입력한다. 이 실제 파일은 `.gitignore`와 `.dockerignore`에 명시되어 Git과 backend Docker build context에 포함하지 않는다.

### 기동과 외부 진입점 — 통과

```bash
docker compose up --build
curl -i http://localhost:8080/
curl -i http://localhost:8080/api
curl -i http://localhost:8080/api/health
curl -i http://localhost:8080/api/auth/session
```

- `docker compose up --build`로 backend가 `healthy`가 된 뒤 Nginx까지 기동했다.
- `GET /`는 HTTP 200으로 frontend 정적 파일을 제공했다.
- `GET /dashboard`는 HTTP 200으로 SPA fallback을 제공했고, 브라우저는 Vue 앱 실행 뒤 URL을 `/`로 정규화했다.
- `GET /api`는 상대 경로 `Location: /api/`를 포함한 HTTP 308을 반환했다. `curl -L`은 같은 `localhost:8080` 진입점을 유지해 backend 루트의 HTTP 404까지 도달했다.
- `GET /api/health`는 Nginx를 거쳐 backend의 `/health`로 전달되고 HTTP 200을 반환했다.
- 비로그인 `GET /api/auth/session`은 HTTP 200 및 `authenticated: false`를 반환했다. 세션 상태 조회는 비로그인 상태를 응답 본문으로 표현한다.
- 보호된 업무 API인 `GET /api/dashboard`와 `GET /api/products/by-barcode`는 비로그인 상태에서 HTTP 401을 반환했다. `/dashboard`는 browser용 SPA 경로이므로 이 API 경계와 다르다.

### Docker 내부 healthcheck — 통과

```bash
docker compose ps
```

- backend healthcheck는 Compose 내부에서 `http://localhost:8000/health`를 호출했고, `healthy` 상태를 확인했다.
- backend가 `healthy`가 된 뒤 Nginx가 기동했다.

### backend 공개 경계 — 통과

```bash
curl -i http://localhost:8000/health
```

- backend에 별도의 호스트 프로세스가 없는 상태에서 위 요청은 연결되지 않았다.
- browser와 외부 요청은 Nginx 공개 포트만 사용한다.

### 인증과 API 요청

- 로그인 화면 렌더링, 비로그인 세션 상태, 보호 API의 차단은 확인했다.
- 로컬 운영자 계정으로 로그인한 뒤 보호 API 요청이 성공하고, 새로고침 뒤에도 로컬 HTTP 세션이 유지되는 것을 수동으로 검증했다.
- 세션 만료 뒤 보호 API 요청은 로그인 화면으로 전환되는 것을 수동으로 검증했다.
- 자동 검증에는 로컬 운영자 자격증명을 사용하지 않았다.
- 이 문서의 검증은 `SESSION_COOKIE_SECURE=false`인 로컬 HTTP 조건만 다룬다.

### SQLite 영속성 — 통과

```bash
docker volume inspect store-expiration-tracker-local_sqlite_data
docker compose restart backend
```

- `sqlite_data` named volume이 backend의 `/app/data`에 마운트된 것을 확인했다.
- SQLite 데이터는 Docker named volume에 저장하여 컨테이너 삭제·재생성과 데이터 생명주기를 분리한다.
- 이 영속성은 컨테이너 생명주기 기준이며, EC2 호스트 자체의 삭제·손실까지 보호하는 것은 아니다.
- backend 컨테이너 재시작 전후 `store_expiration_tracker.db`의 SHA-256이 동일했고, 재시작 뒤 `/api/health`도 HTTP 200을 반환했다.
- `docker compose down -v`는 로컬 named volume 데이터를 삭제하므로 이 검증에 사용하지 않는다.
- 호스트 `data/`는 이미지에 복사하거나 자동 import하지 않는다. 기존 로컬 DB import는 이번 이슈 범위에 포함하지 않는다.

## 설계 보정 사항

- `/api`에 후행 슬래시가 없을 때 Nginx의 자동 리다이렉트가 `:8080`을 잃는 것을 발견했다. `location = /api`와 상대 `Location: /api/` 응답으로 정규화 규칙을 명시해 보정했다.
- 비로그인 세션 조회는 HTTP 401이 아니라 HTTP 200과 `authenticated: false`를 반환한다. 문서의 기대값을 실제 API 계약에 맞췄다.

## 이번 이슈에서 바로 하지 않을 것

- EC2 인스턴스 생성 또는 실제 운영 배포
- 도메인 연결과 HTTPS 인증서 발급
- `SESSION_COOKIE_SECURE=true`의 HTTPS 쿠키 검증
- production secret의 실제 값 기록 또는 주입
- 실제 운영 URL에서 Runbook 실행과 결과 기록
- EBS 연결, 백업, 복구 정책 확정
- staging 환경 추가
- PostgreSQL 등 DB 교체

## 다음 단계

이번 이슈를 닫은 뒤, 로컬 검증에서 실제로 확인된 결과와 남은 조건을 바탕으로 실제 운영 배포 작업을 새 GitHub Issue로 정의한다. 새 Issue 번호나 세부 기술 선택을 미리 확정하지 않는다.

## 관련 문서

- [Issue #20 Review: 배포용 인증/세션 설정 정리](issue-20-deployment-auth-session-policy.md)
- [Issue #21 Review: 로컬/배포 환경변수 기반 연결 설정 분리](issue-21-env-config-separation.md)
- [Issue #22 Review: 운영 배포 공개 범위와 비밀값 운영 기준 정리](issue-22-public-scope-secret-operations.md)
- [Issue #23 Review: 배포 전 인증 검증 체크리스트 정리](issue-23-pre-deploy-auth-checklist.md)
- [Issue #28 SPA fallback and routing policy](issue-28-spa-fallback-routing-policy.md)
