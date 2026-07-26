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
- 현재 서비스 전제는 `단일 점포 / 단일 운영자`다.
- 배포 단계의 접근 제어는 `공개 회원가입 없음 + 로그인만 가능`을 기본 방향으로 잡는다.

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

### users

현재 1차 접근 제어 뼈대에서 사용하는 필드:

- `id`
- `username`
- `password_hash`
- `is_active`
- `created_at`

규칙:

1. 사용자 모델은 접근 제어를 위한 최소 계정 정보만 먼저 가진다.
2. 공개 회원가입은 열지 않는다.
3. 운영자 계정은 seed 또는 직접 주입으로 생성한다.
4. 멀티 점포 확장을 이유로 `store_id`까지 지금 바로 넣지는 않는다.
5. `ADMIN_PASSWORD`, `SESSION_SECRET` 같은 비밀값은 DB에 하드코딩하지 않고 배포 환경변수로 주입한다.

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

### 폐기 없음 처리

- 전제:
  - 대상 상품은 `active`여야 한다.

- 처리:
  - 폐기 이력은 저장하지 않는다.
  - 다음 소비기한을 함께 받으면 `expiration_states.expiration_date`를 새 값으로 갱신한다.
  - 다음 소비기한을 아직 입력하지 않으면 `expiration_states.expiration_date`를 `NULL`로 갱신한다.

- 결과:
  - 새 소비기한을 입력한 경우 상품은 계속 메인 처리 대상 또는 일반 조회 흐름에 남는다.
  - 지금 입력하지 않은 경우 현재 소비기한만 종료되고, 상품은 `미확인` 사이드바 대상으로 이동한다.
  - 이때 상품 row 자체는 유지되며, `expiration_date = NULL`은 다시 확인이 필요한 정상 관리 상태로 해석한다.

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
- 이 API는 실제 폐기 수량이 있는 경우만 담당한다.

### `POST /expiration-checks/no-discard`

역할:

- 현재 소비기한 종료 후 다음 상태 반영

입력:

- `product_id`
- `expiration_date` optional

참고:

- 이 API는 폐기 이력을 저장하지 않는다.
- `expiration_date`가 오면 새 소비기한으로 바로 갱신한다.
- `expiration_date`가 없으면 현재 소비기한을 종료하고 `NULL`로 전환한다.

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

## 6. 접근 제어 방향

현재 논의 기준에서 배포 단계 접근 제어는 아래 원칙으로 정리한다.

1. `GET /health`를 제외한 운영 API는 로그인 뒤에만 접근 가능하게 둔다.
2. 로그인은 브라우저 기반 운영 화면에 맞춰 세션 방식으로 우선 정리한다.
3. 회원가입 화면이나 공개 가입 API는 만들지 않는다.
4. 계정 생성은 운영 절차로 다루고, 앱 기능으로 열지 않는다.
5. 멀티 점포는 추후 확장 가능성으로만 남기고 현재 인증/인가 모델에 섞지 않는다.

### 인증 엔드포인트

1. `POST /auth/login`
2. `POST /auth/logout`
3. `GET /auth/session`

현재 구현 기준은 아래와 같다.

- `POST /auth/login`
  - 입력: `username`, `password`
  - 동작: 인증 성공 시 세션 쿠키를 발급한다.
- `POST /auth/logout`
  - 동작: 세션 쿠키를 삭제한다.
- `GET /auth/session`
  - 동작: 현재 세션 상태를 반환한다.
  - 비로그인 상태여도 `401` 대신 `authenticated: false` 응답을 준다.

### 세션 정책

1. 세션은 로그인 시점부터 최대 `4시간` 동안만 유효한 고정 만료를 우선 기준으로 둔다.
2. 이 시간 기준은 실제 로그인 시점이 대체로 19시 이후라는 운영 흐름을 고려해, 사용 중 불편을 크게 늘리지 않으면서도 퇴근 후 점포 PC에 세션이 오래 남는 위험을 줄이기 위한 상한선으로 본다.
3. 인증 쿠키는 영구 쿠키가 아닌 세션 쿠키를 우선 기준으로 둔다.
4. 브라우저 종료는 세션을 끝낼 수 있는 추가 조건으로 보되, 보안 기준 자체는 `4시간` 고정 만료에 둔다.
5. 사용자가 로그아웃하면 세션 쿠키를 즉시 삭제한다.
6. 무활동 시간 기준 자동 로그아웃은 1차에서는 넣지 않는다.
7. 기기별 세션 정책 분리와 세션 만료 후 재진입 UX는 추후 개선 항목으로 남겨 둔다.

현재 구현은 서버 저장 세션이 아니라, 서명된 세션 쿠키를 검증하는 방식이다.

쿠키 payload에는 최소한의 세션 정보만 넣는다.

- `sub`
- `exp`

### 배포 환경 비밀값

1. `ADMIN_PASSWORD`
2. `SESSION_SECRET`

이 비밀값들은 1차에서는 AWS 비밀 관리 서비스까지 확장하지 않고, 서버 환경변수로 먼저 주입하는 방향을 기준으로 둔다.

### 현재 구현 범위

1. `users` 테이블 추가
2. seed 또는 직접 주입으로 운영자 계정 생성
3. `POST /auth/login`, `POST /auth/logout`, `GET /auth/session` 추가
4. `GET /health`를 제외한 운영 API 보호
5. 프론트 로그인 화면 및 세션 확인 흐름 연결

위 항목은 현재 브랜치 기준으로 모두 반영된 상태다.

### 다음 단계 후보

1. 배포용 `secure` 쿠키와 도메인/호스트 설정 정리
2. 배포 환경 CORS와 프론트 API 주소 분리
3. production `/docs`, `/openapi.json` 비활성화 반영
4. 서버 저장 세션 전환 필요성 검토

## 7. 1차에서 보류하는 API

다음 API는 지금 바로 만들지 않아도 된다.

1. 메인 화면 검색 API
2. 통계 집계 API
3. 카테고리 목록 관리 API
4. 공개 회원가입 API
5. 변경 이력 조회 API

접근 제어 자체는 배포 전 하드닝 범위로 볼 수 있지만, 그 경우에도 공개 회원가입을 먼저 열 필요는 없다.

## 8. 백엔드 구현 시 주의점

1. 중복 바코드 등록은 단순 409 충돌로 끝내지 말고, 프론트가 바로 안내할 수 있는 응답 형태를 고민해야 한다.
2. `NULL`은 비정상 데이터가 아니라 정상 상태이므로, 검증 로직과 응답 모델에서 이를 자연스럽게 허용해야 한다.
3. 아카이브와 복구는 상품 삭제를 대체하는 핵심 동작이므로, 1차 범위에 포함한다.
4. 이후 3개월 폐기 통계를 위해 `category`와 `discard_histories.quantity`는 초기에 잡아두는 편이 낫다.
5. 접근 제어를 추가하더라도 현재 단계에서는 `단일 운영자 로그인`을 먼저 안정적으로 만드는 편이, 멀티 점포나 공개 가입까지 한 번에 여는 것보다 안전하다.
