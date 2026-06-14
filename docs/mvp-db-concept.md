# MVP DB Concept

MVP 구조를 빠르게 맞춰보기 위한 개념 메모다.

## 핵심 구조

- `products`: 추적 대상 상품 마스터
- `expiration_states`: 상품별 현재 소비기한 정보 1개
- `discard_histories`: 폐기 이력 누적 기록

```text
+----------------------+
| products             |
+----------------------+
| PK id                |
| barcode              |
| name                 |
| status               |
| archived_at          |
+----------------------+
          |
          | 1 : 1
          v
+----------------------+
| expiration_states    |
+----------------------+
| PK id                |
| FK product_id        |
| expiration_date      |
| updated_at           |
+----------------------+

+----------------------+
| products             |
+----------------------+
| PK id                |
+----------------------+
          |
          | 1 : N
          v
+----------------------+
| discard_histories    |
+----------------------+
| PK id                |
| FK product_id        |
| discarded_date       |
| quantity             |
+----------------------+
```

## 테이블별 핵심 필드

### `products`

| 필드 | 의미 |
| --- | --- |
| `id` | 상품 식별자 |
| `barcode` | 바코드 |
| `name` | 상품명 |
| `status` | 현재 사용 상태 |
| `archived_at` | 보관 종료 시점 |

### `expiration_states`

| 필드 | 의미 |
| --- | --- |
| `id` | 상태 row 식별자 |
| `product_id` | 어떤 상품의 현재 소비기한 상태인지 연결 |
| `expiration_date` | 현재 추적 중인 소비기한. 비어 있으면 아직 다음 소비기한이 없는 상태 |
| `updated_at` | 마지막 갱신 시점 |

### `discard_histories`

| 필드 | 의미 |
| --- | --- |
| `id` | 폐기 이력 식별자 |
| `product_id` | 어떤 상품의 폐기 이력인지 연결 |
| `discarded_date` | 폐기한 날짜 |
| `quantity` | 폐기 수량 |

## 이 문서에서 전제하는 규칙

1. 상품은 삭제하지 않고 계속 남긴다.
2. 각 상품은 현재 소비기한 상태 row를 하나만 가진다.
3. `expiration_date`가 있으면 현재 추적 중인 소비기한이 있는 상태다.
4. `expiration_date`가 `NULL`이면 다음 소비기한이 아직 없거나 확인되지 않은 상태다.
5. `expired`, `due_today`, `due_tomorrow` 같은 분류는 컬럼으로 저장하지 않고 조회할 때 계산한다.
