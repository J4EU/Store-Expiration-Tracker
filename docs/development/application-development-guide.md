# Application Development Guide

이 문서는 애플리케이션 코드를 수정할 때 먼저 볼 위치와 책임 경계를 안내한다. 정확한 구현 세부사항을 복제하는 문서가 아니라, 코드 탐색 지도다.

## 전체 흐름

로컬 개발에서는 아래 경로로 요청이 흐른다.

```text
Browser
  -> Vue application (frontend/src/)
  -> frontend/src/api.js
  -> /api/...
  -> Vite development proxy
  -> FastAPI application (backend/app/main.py)
  -> SQLite (backend/data/store_expiration_tracker.db)
```

이 흐름은 로컬 개발 기준이다. production 배포 구조와 검증 상태는 이 문서의 범위가 아니다.

## 코드 위치와 책임

| 수정하려는 것 | 먼저 볼 위치 | 책임 |
| --- | --- | --- |
| API 진입점과 처리 흐름 | `backend/app/main.py` | FastAPI route, 인증 의존성 연결, 도메인 처리 조합 |
| 인증과 세션 | `backend/app/auth.py` | 운영자 인증, 세션 생성·검증, 쿠키 처리 |
| 런타임 설정 | `backend/app/settings.py`, `deploy/dev/backend.env.example` | 개발·production 환경별 설정 읽기와 예시 값 |
| DB 연결과 초기화 | `backend/app/db.py` | DB 경로, 연결, 시작 시 스키마 초기화 |
| API schema | `backend/app/schemas.py` | request/response 모델과 입력 검증 |
| DB 구조 | `backend/db/schema.sql` | table, constraint, trigger, index |
| 화면 상태와 사용자 상호작용 | `frontend/src/App.vue` | 로그인, 대시보드, 등록, 처리, 아카이브 화면 흐름 |
| API 호출 | `frontend/src/api.js` | API base URL, HTTP 요청, 오류 처리 |
| 화면 스타일 | `frontend/src/styles.css` | Vue 화면의 CSS |
| Frontend 개발 서버 | `frontend/vite.config.js` | Vite 포트와 `/api` proxy |

## 수정 전에 확인할 경계

### Product 규칙과 구현을 구분한다

상품을 보존하고 아카이브로 전환하는 방식, 소비기한이 없는 상태의 의미, 폐기와 폐기 없음의 구분은 단순 UI 선택이 아니라 제품 규칙에 영향을 준다. 이런 동작을 바꾸기 전에는 현재 Product 문서와 관련 Issue를 함께 확인하고, 코드만 보고 정책을 새로 만들지 않는다.

반대로 정확한 endpoint, schema field, SQL constraint, trigger, index는 이 문서가 아니라 코드가 기준이다.

- API 계약: 실행 중인 `http://localhost:8000/docs`, `backend/app/main.py`, `backend/app/schemas.py`
- DB 구조: `backend/db/schema.sql`
- 실제 화면 동작: `frontend/src/`

### Backend와 Frontend를 함께 바꿔야 하는 경우

API contract가 바뀌면 `backend/app/main.py`와 `backend/app/schemas.py`만 수정하고 끝내지 않는다. 해당 요청을 보내거나 응답을 해석하는 `frontend/src/api.js`와 `frontend/src/App.vue`도 함께 확인한다.

화면만 바꿔도 API 호출 순서, 로그인 상태, 오류 처리에 영향을 줄 수 있다. 먼저 `App.vue`에서 호출 지점을 찾고, `api.js`를 거쳐 Backend route와 schema까지 확인한다.

### 환경 설정을 바꿀 때

로컬 설정 예시는 `deploy/dev/backend.env.example`과 `frontend/.env.example`에 있다. 실제 `.env` 값은 커밋하지 않는다.

`VITE_` 환경변수는 Frontend build/dev-server 쪽 설정이고, Backend 환경변수와 다른 시점에 읽힌다. Vite 설정이나 `frontend/.env`를 바꿨다면 개발 서버를 다시 시작해 반영 여부를 확인한다.

## 코드 변경 뒤 최소 확인 경로

변경 범위에 따라 필요한 확인은 달라진다. 최소한 관련 서버를 실행한 뒤 아래 경로가 깨지지 않는지 확인한다.

1. Backend 변경이면 `GET /health`와 해당 API contract를 확인한다.
2. Frontend 변경이면 브라우저에서 로그인 뒤 변경한 흐름을 확인한다.
3. API 또는 schema 변경이면 Frontend 호출부와 OpenAPI 문서를 함께 확인한다.
4. DB schema 변경이면 새 DB 초기화와 기존 DB에 대한 영향 범위를 별도로 검토한다.

배포, Terraform, EC2/EBS, 실제 production 동작은 Development 문서의 source of truth가 아니다. 해당 작업은 관련 Infrastructure·Operations 문서와 설정을 기준으로 다룬다.
