# Backend Quickstart

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

서버를 실행하면 DB 파일은 `data/store_expiry_manager.db`에 자동 생성된다.
API 문서는 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)에서 확인할 수 있다.

## 프론트 개발 서버

```bash
cd frontend
npm install
npm run dev
```

Vue 개발 서버 기본 주소는 [http://127.0.0.1:5173](http://127.0.0.1:5173)이다.
로컬 개발 편의를 위해 백엔드에는 `5173` 기준 CORS를 열어둔다.

## 현재 위치

- 백엔드는 FastAPI 기반으로 구현한다.
- 프론트엔드는 `frontend/`의 Vue 앱으로 별도 개발한다.
- API 범위와 상태 규칙은 `docs/backend-implementation-guide.md`를 기준으로 맞춘다.
- 프론트 1차 화면 범위는 `docs/frontend-v1-implementation.md`를 기준으로 맞춘다.

## 현재 API

- `GET /health`
- `GET /products/by-barcode`
- `POST /products`
- `GET /dashboard`
- `PATCH /products/{product_id}`
- `PATCH /products/{product_id}/expiration`
- `POST /discards`
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
  "category": "푸드",
  "expiration_date": "2026-06-15"
}
```

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
