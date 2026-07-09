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
uvicorn app.main:app --reload
```

서버를 실행하면 DB 파일은 `data/store_expiration_tracker.db`에 자동 생성된다.
API 문서는 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)에서 확인할 수 있다.

## 프론트 개발 서버

```bash
cd frontend
npm install
npm run dev
```

Vue 개발 서버 기본 주소는 [http://127.0.0.1:5173](http://127.0.0.1:5173)이다.
로컬 개발 편의를 위해 백엔드에는 `5173` 기준 CORS를 열어둔다.

## 빠른 확인 순서

1. 백엔드 서버를 실행한다.
2. 별도 터미널에서 프론트 개발 서버를 실행한다.
3. 브라우저에서 [http://127.0.0.1:5173](http://127.0.0.1:5173)로 접속한다.
4. `등록 시작 -> 바코드 조회 -> 소비기한 반영 -> 오늘 처리/미확인 확인` 흐름으로 기본 동작을 본다.

## 현재 위치

- 백엔드는 FastAPI 기반으로 구현한다.
- 프론트엔드는 `frontend/`의 Vue 앱으로 별도 개발한다.
- API 범위와 상태 규칙은 `docs/backend-implementation-guide.md`를 기준으로 맞춘다.
- 프론트 화면 범위는 `docs/frontend-implementation-guide.md`를 기준으로 맞춘다.

## 현재 API

- `GET /health`
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
