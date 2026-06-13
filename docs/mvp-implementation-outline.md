# MVP Implementation Outline

## 문서 목적

이 문서는 `docs/mvp.md`를 바탕으로, 실제 구현에 바로 옮길 수 있는 운영 규칙을 정리합니다.

핵심 범위는 아래 세 가지입니다.

1. 상태 전이 규칙
2. DB 스키마 초안
3. 메인 대시보드 조회 기준

## 1. 상태 전이 규칙

### 상품 상태

- `active`: 현재 추적 대상인 상품
- `archived`: 더 이상 기본 운영 화면에서 추적하지 않는 상품

### 현재 소비기한 상태

- `tracked`: 현재 소비기한이 등록된 상태
- `empty`: 다음 소비기한이 비어 있지만 계속 추적해야 하는 상태

### 상태 전이표

```text
active + tracked(date)
  -> 폐기 처리
  -> 다음 소비기한 입력: active + tracked(new_date)
  -> 다음 소비기한 없음: active + empty

active + empty
  -> 소비기한 확인됨: active + tracked(date)
  -> 관리 중단: archived + empty

active + tracked(date)
  -> 관리 중단: archived + empty

archived + empty
  -> 다시 관리 시작: active + empty
```

### 전이 원칙

1. 폐기 처리는 반드시 다음 상태 입력과 함께 완료합니다.
2. 다음 상태는 `새 소비기한 입력` 또는 `empty 적용` 중 하나여야 합니다.
3. 상품은 삭제하지 않고 `active`와 `archived` 사이에서만 전환합니다.
4. 아카이브 복구 시 기본 상태는 `active + empty`입니다.

## 2. DB 스키마 초안

### products

상품 마스터 테이블입니다.

```text
products
- id
- barcode unique
- name
- status active|archived
- archived_at nullable
```

설명:

- `barcode`: 사용자 기준의 상품 식별값
- `status`: 현재 운영 대상인지 여부
- `archived_at`: 아카이빙 시점 기록

### expiration_states

상품별 현재 소비기한 상태를 저장하는 테이블입니다.

```text
expiration_states
- id
- product_id unique
- expiration_date nullable
- state tracked|empty
- updated_at
```

설명:

- 각 상품은 현재 소비기한 상태 row를 하나만 가집니다.
- `state = tracked`이면 `expiration_date`가 채워집니다.
- `state = empty`이면 `expiration_date`는 비울 수 있습니다.
- 소비기한이 바뀌면 새 row를 추가하지 않고 기존 row를 갱신합니다.

### discard_histories

폐기 이력을 누적 저장하는 테이블입니다.

```text
discard_histories
- id
- product_id
- discarded_date
- quantity
```

설명:

- 폐기 이력은 `언제`, `어떤 상품이`, `몇 개` 폐기되었는지 기록합니다.
- 이 테이블은 현재 상태와 별개로 누적됩니다.
- 향후 `최근 3개월 기준 상품별 폐기 수량` 집계의 기반이 됩니다.

## 3. 메인 대시보드 조회 기준

메인 대시보드는 MVP의 중심 화면입니다.

운영상 중요한 것은 단순히 `오늘 + 내일`을 보는 것이 아니라, **이미 소비기한이 지났지만 아직 상태가 갱신되지 않은 상품까지 함께 조회하는 것**입니다.

### 섹션 1. 처리 대상

조건:

- `products.status = active`
- `expiration_states.state = tracked`
- `expiration_states.expiration_date <= tomorrow`

이 섹션에는 아래 상품이 모두 포함됩니다.

- 이미 소비기한이 지난 상품
- 오늘까지인 상품
- 내일까지인 상품

### 섹션 2. 미확인 대상

조건:

- `products.status = active`
- `expiration_states.state = empty`

이 섹션은 다음 소비기한을 아직 확인하지 못한 상품을 보여줍니다.

### 운영 메모

1. 일부 상품은 점포 운영 원칙에 따라 소비기한 전날 폐기할 수 있습니다.
2. 따라서 `expiration_date <= tomorrow` 조건이 필요합니다.
3. `empty` 상품은 날짜 비교가 아니라 별도 섹션으로 관리합니다.

## 4. 구현 시 확인할 사항

1. 폐기 처리 UI에서 `수량 입력 -> 다음 소비기한 입력 또는 empty 적용`이 한 흐름으로 이어져야 합니다.
2. 메인 대시보드에서 처리 대상과 미확인 대상을 분리해 보여주더라도, 상태 저장 규칙은 단순하게 유지합니다.
3. 분석 기능은 MVP 범위 밖이지만, 폐기 이력은 이후 집계를 고려해 누적 저장합니다.
