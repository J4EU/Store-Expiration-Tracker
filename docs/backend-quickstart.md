# Backend Quickstart

백엔드 실행과 로컬 확인에 가장 먼저 쓰는 문서입니다.

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 실행

```bash
export ADMIN_PASSWORD='change-this-password'
export SESSION_SECRET='change-this-session-secret'
uvicorn app.main:app --reload
```

서버를 실행하면 DB 파일은 `data/store_expiration_tracker.db`에 자동 생성된다.
API 문서는 [http://localhost:8000/docs](http://localhost:8000/docs)에서 확인할 수 있다.

현재 로컬 실행에도 아래 접근 제어 기준을 반영한다.

- 공개 회원가입은 두지 않는다.
- 운영자 계정은 초기 seed 또는 직접 주입으로 생성한다.
- `GET /health`를 제외한 운영 API는 로그인 뒤에만 접근 가능하게 둔다.
- `ADMIN_PASSWORD`, `SESSION_SECRET` 환경변수는 서버 시작 전에 반드시 주입한다.
- 초기 세션은 로그인 시점부터 최대 `4시간` 동안만 유효한 고정 만료를 둔다.
- 인증 쿠키는 영구 저장하지 않는 세션 쿠키를 둔다.
- 브라우저 종료는 세션을 끝낼 수 있는 추가 조건으로 보고, 보안 기준 자체는 `4시간` 고정 만료에 둔다.
- 무활동 자동 로그아웃은 1차에서는 넣지 않는다.
- 세션 만료 후 재진입 UX는 추후 개선 항목으로 남겨 둔다.
- 현재 전제는 `단일 점포 / 단일 운영자`다.

1차 인증 엔드포인트는 아래 범위로 둔다.

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/session`

## 프론트 개발 서버

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Vue 개발 서버 기본 주소는 [http://localhost:5173](http://localhost:5173)이다.
프론트 API 주소는 `VITE_API_BASE_URL`로 명시하며, 로컬 개발 기본값은 `/api`이다.
로컬 개발 편의를 위해 백엔드에는 `5173` 기준 CORS를 열어둔다.

## 빠른 확인 순서

1. 백엔드 서버를 실행한다.
2. 별도 터미널에서 프론트 개발 서버를 실행한다.
3. 브라우저에서 [http://localhost:5173](http://localhost:5173)로 접속한다.
4. 로그인 화면에서 기본 운영자 계정 `admin`과 서버에 설정한 비밀번호로 로그인한다.
5. `등록 시작 -> 바코드 조회 -> 소비기한 반영 -> 오늘 처리/미확인 확인` 흐름으로 기본 동작을 본다.

로컬 테스트에서는 프론트와 API 요청을 같은 프론트 origin 아래에서 확인한다.

- 기본 확인 기준은 브라우저에서 `localhost:5173/api/...`로 요청이 나가는 흐름이다.
- Vite dev server는 `/api` prefix를 제거해 `http://localhost:8000/...`으로 프록시한다.
- API 문서는 백엔드에 직접 접속해 [http://localhost:8000/docs](http://localhost:8000/docs)에서 확인한다.
- 현재 MVP의 공식 프론트 화면 URL은 `/` 하나이며, fallback으로 열린 `/auth/session`, `/dashboard` 같은 경로는 앱 부팅 시 `/`로 정규화한다.
- production 빌드는 `VITE_API_BASE_URL=/api`를 기준으로 두며, 실제 `/api` reverse proxy 구현과 검증은 배포 구조가 확정된 뒤 별도로 진행한다.

## 현재 위치

- 백엔드는 FastAPI 기반으로 구현한다.
- 프론트엔드는 `frontend/`의 Vue 앱으로 별도 개발한다.
- API 범위와 상태 규칙은 `docs/backend-implementation-guide.md`를 기준으로 맞춘다.
- 프론트 화면 범위는 `docs/frontend-implementation-guide.md`를 기준으로 맞춘다.

## 현재 API

- `GET /health`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/session`
- `GET /products/by-barcode`
- `POST /products`
- `GET /dashboard`
- `PATCH /products/{product_id}`
- `PATCH /products/{product_id}/expiration`
- `POST /discards`
- `POST /expiration-checks/no-discard`
- `PATCH /products/{product_id}/archive`
- `PATCH /products/{product_id}/restore`
- `GET /archived-products`

현재 API 목록은 구현 진행에 따라 변경될 수 있다.
구현 기준으로는 아카이브/복구/상품 수정/아카이브 조회 API도 1차 범위에 포함한다.

위 API 중 `GET /health`만 공개이고, 나머지는 로그인 필요 API다.

배포 시 비밀값은 우선 아래 항목을 서버 환경변수로 주입하는 방향을 기준으로 본다.

- `ADMIN_PASSWORD`
- `SESSION_SECRET`

## 예시 요청

### 상품 등록

```json
POST /products
{
  "barcode": "8801234567890",
  "name": "삼각김밥",
  "category": "미선택",
  "expiration_date": "2026-06-15"
}
```

현재 카테고리 입력값은 `미선택` 또는 `유제품`만 허용한다.

### 바코드 조회

```text
GET /products/by-barcode?barcode=8801234567890
```

### 대시보드 조회

```text
GET /dashboard?reference_date=2026-06-14
```

### 폐기 처리 후 다음 상태 반영

`discarded_date`는 요청 본문으로 받지 않고, 폐기 저장 시점의 날짜를 서버가 자동 기록한다.

```json
POST /discards
{
  "product_id": 1,
  "quantity": 2
}
```

### 폐기 없음 처리 후 다음 상태 반영

`폐기 없음`은 소비기한은 확인했지만 이미 판매되어 폐기할 수량이 없을 때 사용한다.

이 경우 폐기 이력은 저장하지 않는다.
다만 근무자가 바로 다음 상품의 소비기한을 확인할 가능성이 높으므로, 새 소비기한을 함께 보낼 수 있게 둔다.

- 새 소비기한을 함께 보내면 바로 갱신한다.
- 아직 확인하지 못했다면 현재 소비기한만 종료해 `expiration_date = NULL` 상태로 전환한다.

`expiration_date = NULL`은 오류가 아니라 이후 다시 확인할 `미확인` 상태이므로, 이 흐름에서는 다음 소비기한 입력을 강제하지 않아도 된다.

```json
POST /expiration-checks/no-discard
{
  "product_id": 1,
  "expiration_date": "2026-06-29"
}
```
