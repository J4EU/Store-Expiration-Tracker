# Backend Implementation Guide

## 문서 목적

이 문서는 현재 MVP 기준에서 백엔드가 제공해야 할 데이터 규칙과 API 범위를 정리한다.

목적은 아래와 같다.

1. 프론트 Vue 1차 구현에 필요한 백엔드 범위를 고정한다.
2. 상태 전이 규칙을 API 수준에서 명확히 한다.
3. 구현 전에 필요한 판단을 문서로 남긴다.

## 1. 현재 전제

- 1차 목표는 `로컬 검증용 MVP`다.
- 핵심 요구는 `한 번 등록한 상품이 시스템에서 사라지지 않는 것`이다.
- 상품은 삭제하지 않고 `active / archived` 상태로 관리한다.
- `expiration_date = NULL`은 오류가 아니라 `미확인` 상태다.

## 2. 데이터 모델 기준

### products

필드:

- `id`
- `barcode`
- `name`
- `category`
- `status`
- `archived_at`

규칙:

1. 바코드는 유일해야 한다.
2. 상품명은 수정 가능하다.
3. 카테고리는 1차에서 `유제품` 또는 `미선택`만 사용한다.
4. 상품은 삭제하지 않는다.

### expiration_states

필드:

- `id`
- `product_id`
- `expiration_date`
- `updated_at`

규칙:

1. 각 상품은 현재 소비기한 상태 row를 하나만 가진다.
2. `expiration_date IS NULL`이면 `미확인` 상태다.
3. `NULL`은 `다음 상품이 없음`과 `아직 확인 못함`을 구분하지 않고 함께 표현한다.

### discard_histories

필드:

- `id`
- `product_id`
- `discarded_date`
- `quantity`

규칙:

1. 폐기 이력은 누적 저장한다.
2. 1차에서는 변경 이력 전체보다 `폐기 수량 집계 가능성`을 더 중요하게 본다.
3. 이후 `최근 3개월 동안 어떤 상품이 몇 개 폐기되었는지` 분석할 수 있어야 한다.

## 3. 상태 전이 규칙

### 상품 등록

- 새 상품 등록
  - `active`
  - `expiration_date = 입력값 또는 NULL`

- 중복 바코드 등록 시
  - 새 상품을 만들지 않는다.
  - 기존 상품 정보를 반환한다.

### 소비기한 갱신

- `active + expiration_date NULL`
  - 소비기한 확인됨
  - `active + expiration_date 있음`

- `active + expiration_date 있음`
  - 날짜 수정
  - `active + 새 expiration_date`

### 폐기 처리

- 전제:
  - 대상 상품은 `active`여야 한다.

- 처리:
  - `discarded_date`는 요청값이 아니라 폐기 저장 시점의 오늘 날짜로 기록
  - `discard_histories`에 기록 추가
  - `expiration_states.expiration_date`를 `NULL`로 갱신

- 결과:
  - 폐기 직후 상품은 `미확인` 사이드바 대상으로 이동한다.

### 아카이빙

- `active`
  - 아카이브 전환
  - `archived + expiration_date NULL`

### 복구

- `archived`
  - 복구
  - `active + expiration_date NULL`

## 4. 대시보드 조회 규칙

기준 날짜를 `reference_date`라고 둔다.

### 처리 대상

조건:

- `products.status = active`
- `expiration_date IS NOT NULL`

역할:

- 기본 진입에서는 오늘 우선 처리할 대상을 확인한다.
- 필요할 때는 `전체` 필터로 현재 소비기한 데이터가 어떤 상태로 저장되어 있는지도 함께 조회한다.
- `유제품` 카테고리 상품은 `내일 만료`여도 오늘 처리 대상으로 포함할 수 있어야 한다.

분류:

- 지난 상품
- 오늘 만료
- 내일 상품
- 이후 상품

정렬:

1. 지난 상품
2. 오늘 만료
3. 내일 상품
4. 이후 상품
5. 같은 분류 안에서는 `expiration_date` 오름차순

### 미확인 대상

조건:

- `products.status = active`
- `expiration_date IS NULL`

정렬:

- 최근 확인이 오래된 순 또는 `updated_at` 기준 오름차순

## 5. 1차 API 범위

### `POST /products`

역할:

- 바코드 기반 상품 등록

입력:

- `barcode`
- `name` optional
- `expiration_date` optional
- `category` optional

반환:

- 신규 등록 상품 정보

중복 바코드 처리:

- HTTP 오류만 던지지 않는다.
- 프론트가 바로 안내할 수 있도록 `이미 등록된 상품 정보`를 함께 응답한다.

생성 규칙:

- 바코드가 기존 상품과 매칭되면 새 상품을 만들지 않는다.
- 신규 상품 생성이 필요한 경우에만 `name` 입력이 필요하다.

### `GET /products/by-barcode`

역할:

- 바코드 기반 등록 흐름에서 기존 상품 존재 여부 확인

입력:

- `barcode`

반환:

- `found`
- `product` optional

### `GET /dashboard`

역할:

- 기준 날짜의 처리 대상과 미확인 대상을 함께 조회

입력:

- `reference_date`

반환:

- 기준 날짜
- 처리 기준 날짜 범위
- 처리 대상 목록
- 미확인 대상 목록

### `PATCH /products/{product_id}`

역할:

- 상품명 수정

1차 범위:

- `name` 수정

### `PATCH /products/{product_id}/expiration`

역할:

- 현재 소비기한 갱신

사용 상황:

- 미확인 상품에 소비기한 입력
- 기존 소비기한 수정

### `POST /discards`

역할:

- 폐기 이력 저장 후 다음 상태 반영

입력:

- `product_id`
- `quantity`

참고:

- `discarded_date`는 API 입력값이 아니라 폐기 저장 시점의 오늘 날짜를 서버가 기록한다.

### `PATCH /products/{product_id}/archive`

역할:

- 활성 상품을 아카이브 전환

규칙:

- 상태를 `archived`로 바꾼다.
- 현재 소비기한은 `NULL`로 비운다.

### `PATCH /products/{product_id}/restore`

역할:

- 아카이브 상품 복구

규칙:

- 상태를 `active`로 바꾼다.
- 현재 소비기한은 `NULL`로 둔다.

### `GET /archived-products`

역할:

- 아카이브 목록 조회

입력:

- `query` optional

검색 범위:

- 바코드
- 상품명
- 카테고리

## 6. 1차에서 보류하는 API

다음 API는 지금 바로 만들지 않아도 된다.

1. 메인 화면 검색 API
2. 통계 집계 API
3. 카테고리 목록 관리 API
4. 사용자/권한 API
5. 변경 이력 조회 API

## 7. 백엔드 구현 시 주의점

1. 중복 바코드 등록은 단순 409 충돌로 끝내지 말고, 프론트가 바로 안내할 수 있는 응답 형태를 고민해야 한다.
2. `NULL`은 비정상 데이터가 아니라 정상 상태이므로, 검증 로직과 응답 모델에서 이를 자연스럽게 허용해야 한다.
3. 아카이브와 복구는 상품 삭제를 대체하는 핵심 동작이므로, 1차 범위에 포함한다.
4. 이후 3개월 폐기 통계를 위해 `category`와 `discard_histories.quantity`는 초기에 잡아두는 편이 낫다.
