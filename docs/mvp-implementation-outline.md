# MVP Implementation Outline

## 문서 목적

이 문서는 `docs/mvp.md`를 바탕으로, 실제 구현에 바로 옮길 수 있는 운영 규칙을 정리한다.

핵심 범위는 아래 세 가지이다.

1. 상태 전이 규칙
2. DB 스키마 초안
3. 메인 대시보드 조회 기준

## 1. 상태 전이 규칙

### 상품 상태

- `active`: 현재 추적 대상인 상품
- `archived`: 더 이상 기본 운영 화면에서 추적하지 않는 상품

### 현재 소비기한 상태

- `expiration_date`가 있으면 현재 소비기한이 등록된 상태
- `expiration_date`가 `NULL`이면 다음 소비기한이 비어 있지만 계속 추적해야 하는 상태
- 처음 상품 등록 시에도 `expiration_date = NULL`로 시작할 수 있다.

### 상태 전이표

```text
active + expiration_date 있음
  -> 폐기 처리
  -> 다음 소비기한 입력: active + 새 expiration_date
  -> 다음 소비기한 없음: active + expiration_date NULL

active + expiration_date NULL
  -> 소비기한 확인됨: active + expiration_date 있음
  -> 관리 중단: archived + expiration_date NULL

active + expiration_date 있음
  -> 관리 중단: archived + expiration_date NULL

archived + expiration_date NULL
  -> 다시 관리 시작: active + expiration_date NULL
```

### 전이 원칙

1. 소비기한 등록 흐름의 시작점은 상품명 입력이 아니라 바코드 입력이다.
2. 바코드가 기존 상품과 매칭되면 기존 상품 상태 갱신으로 이어진다.
3. 바코드가 없을 때만 신규 상품 생성 입력으로 넘어간다.
4. 폐기 처리는 반드시 다음 상태 입력과 함께 완료한다.
5. 다음 값은 `새 소비기한 입력` 또는 `expiration_date = NULL` 적용 중 하나여야 한다.
6. 상품은 삭제하지 않고 `active`와 `archived` 사이에서만 전환한다.
7. 아카이브 복구 시 기본값은 `active + expiration_date NULL`이다.
8. 아카이빙은 주로 `재고 0 + 한동안 발주 X` 같은 현장 판단에 따라 수동으로 수행한다.

## 2. DB 스키마 초안

### products

상품 마스터 테이블이다.

```text
products
- id
- barcode unique
- name
- category nullable
- status active|archived
- archived_at nullable
```

설명:

- `barcode`: 사용자 기준의 상품 식별값
- `category`: 1차에서는 자유입력 문자열
- `status`: 현재 운영 대상인지 여부
- `archived_at`: 아카이빙 시점 기록
- 상품은 소비기한 없이 먼저 생성할 수 있다.
- 동일 바코드 등록 시 새 row를 만들지 않고 기존 상품 정보를 안내한다.

### expiration_states

상품별 현재 소비기한 상태를 저장하는 테이블이다.

```text
expiration_states
- id
- product_id unique
- expiration_date nullable
- updated_at
```

설명:

- 각 상품은 현재 소비기한 상태 row를 하나만 가진다.
- `expiration_date`가 채워져 있으면 현재 추적 중인 소비기한이 있는 상태다.
- `expiration_date`가 `NULL`이면 다음 소비기한이 아직 없거나 확인되지 않은 상태다. 프론트 용어는 `미확인`으로 둔다.
- 소비기한이 바뀌면 새 row를 추가하지 않고 기존 row를 갱신한다.
- `NULL`은 다시 확인이 필요한 정상 상태다.

### discard_histories

폐기 이력을 누적 저장하는 테이블이다.

```text
discard_histories
- id
- product_id
- discarded_date
- quantity
```

설명:

- 폐기 이력은 `언제`, `어떤 상품이`, `몇 개` 폐기되었는지 기록한다.
- 이 테이블은 현재 상태와 별개로 누적된다.
- 향후 `최근 3개월 기준 상품별 폐기 수량` 집계의 기반이 된다.

## 3. 메인 대시보드 조회 기준

메인 대시보드는 MVP의 중심 화면이다.

운영상 중요한 것은 단순히 `오늘 + 내일`을 보는 것이 아니라, **이미 소비기한이 지났지만 아직 상태가 갱신되지 않은 상품까지 함께 조회하는 것**이다.
또한 `NULL` 상품은 별도 탭으로 보내지 않고, 같은 화면 안의 분리된 레이아웃에서 바로 확인할 수 있어야 한다.

기본 화면 구조는 아래와 같다.

- 상단: 상품 등록
- 메인: 처리 대상
- 우측 사이드바: `미확인`

### 섹션 1. 처리 대상

조건:

- `products.status = active`
- `expiration_states.expiration_date <= tomorrow`

이 섹션에는 아래 상품이 모두 포함된다.

- 이미 소비기한이 지난 상품
- 오늘까지인 상품
- 내일까지인 상품

기본 정렬 우선순위는 아래와 같다.

1. 지난 상품
2. 오늘 만료
3. 내일 상품

### 섹션 2. 미확인 대상

조건:

- `products.status = active`
- `expiration_states.expiration_date IS NULL`

이 섹션은 다음 소비기한을 아직 확인하지 못한 상품을 보여준다.
이 섹션은 처리 대상 섹션과 분리되지만, 메인 대시보드의 같은 화면 안에 함께 배치된다.
여러 탭으로 이동하지 않고 한 화면 안에서 바로 오갈 수 있어야 한다.

### 운영 메모

1. 일부 상품은 점포 운영 원칙에 따라 소비기한 전날 폐기할 수 있다.
2. 따라서 `expiration_date <= tomorrow` 조건이 필요하다.
3. `expiration_date`가 `NULL`인 상품은 날짜 비교가 아니라 같은 화면 안의 별도 섹션으로 관리한다.

## 4. 구현 시 확인할 사항

1. 폐기 처리 UI에서 `수량 입력 -> 다음 소비기한 입력 또는 expiration_date NULL 적용`이 한 흐름으로 이어져야 한다.
2. 메인 대시보드에서 처리 대상과 미확인 대상을 분리해 보여주더라도, 상태 저장 규칙은 단순하게 유지한다.
3. 메인 화면 날짜 입력은 캘린더보다 숫자 직접 입력 중심 UX를 우선 검토한다.
4. 상품 등록 중복 시에는 실패 처리만 하지 말고 기존 상품 정보를 바로 안내할 수 있어야 한다.
5. 분석 기능은 MVP 범위 밖이지만, 폐기 이력은 이후 집계를 고려해 누적 저장한다.
