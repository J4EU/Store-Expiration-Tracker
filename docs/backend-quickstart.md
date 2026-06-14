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

## 현재 API

- `GET /health`
- `POST /products`
- `GET /dashboard`
- `POST /discards`

## 예시 요청

### 상품 등록

```json
POST /products
{
  "barcode": "8801234567890",
  "name": "삼각김밥",
  "expiration_date": "2026-06-15"
}
```

### 대시보드 조회

```text
GET /dashboard?reference_date=2026-06-14
```

### 폐기 처리 후 다음 상태 반영

```json
POST /discards
{
  "product_id": 1,
  "discarded_date": "2026-06-14",
  "quantity": 2,
  "next_expiration_date": null
}
```
