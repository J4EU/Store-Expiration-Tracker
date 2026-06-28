# Store-Expiration-Tracker

편의점에서 상품별 소비기한 상태를 끊기지 않게 추적하기 위한 프로젝트입니다.

이 저장소는 문제 정의, MVP 설계, 그리고 실제 로컬 검증용 구현을 함께 다룹니다. 목표는 전체 재고 관리 시스템을 만드는 것이 아니라, 한 번 등록한 상품이 소비기한 값이 있든 없든 추적 대상에서 사라지지 않도록 하는 것입니다.

## 왜 필요한가

기존 POS에도 소비기한 등록 기능은 있지만, 실제 운영에서는 상품별 현재 상태를 계속 유지하기 어렵습니다.

특히 다음에 등록할 소비기한이 없는 상태에서 품목을 삭제하면, 소비기한 정보뿐 아니라 그 상품이 다시 확인이 필요한 대상이라는 사실도 함께 사라집니다. 그 결과 근무자는 "내가 어떤 상품을 지웠지?", "어떤 상품을 다시 확인해야 하지?"를 기억에 의존하게 됩니다. 이 프로젝트는 그 인지 소모를 줄이기 위한 도구를 만드는 데 초점을 둡니다.

핵심은 단순히 소비기한 날짜를 저장하는 것이 아니라, 어떤 상품이 지금 `확인됨` 상태인지 `미확인` 상태인지가 시스템에 계속 남아 있도록 만드는 것입니다.

## 현재 범위

현재 MVP에서 다루는 범위는 아래와 같습니다.

- 상품별 현재 소비기한 상태 추적
- `expiration_date = NULL`도 정상적인 `미확인` 상태로 유지
- 오늘 확인이 필요한 소비기한 있는 상품과 `미확인` 상품의 분리 조회
- 바코드 기반 소비기한 등록 흐름과 필요 시 신규 상품 등록
- `폐기 완료` 처리 후 `미확인` 전환
- `폐기 없음` 처리 후 다음 소비기한 즉시 입력 또는 `미확인` 전환
- 상품 아카이빙과 재활성화
- 폐기 데이터 누적 저장

다음 항목은 현재 범위에 포함하지 않습니다.

- 편의점 전체 재고 관리
- 발주 기능
- 매출 및 판매 분석 기능
- 복잡한 분석 대시보드

## 현재 상태

현재는 Vue 기반 프론트엔드와 FastAPI 백엔드로 로컬 검증 가능한 MVP를 구현해 둔 상태입니다.

현재 운영 화면의 핵심 구조는 `좌측 사이드바 상품 등록 + 메인 처리 대상 + 좌측 미확인 사이드바` 입니다.

메인 처리 대상에서는 아래 흐름을 다룹니다.

- `폐기 완료`: 실제 폐기 수량 저장 후 `미확인` 전환
- `폐기 없음`: 이미 판매되어 폐기할 수량이 없을 때, 다음 소비기한을 바로 입력하거나 `미확인`으로 넘기기

이후에는 누적된 폐기 데이터를 바탕으로 발주 판단에 참고할 수 있는 구조로 확장하는 방향을 염두에 두고 있습니다.

현재 프론트엔드 소스는 `frontend/`, 백엔드 소스는 `app/`에 있습니다.

## 문서

### 핵심 문서

처음 읽는 사람이라면 아래 문서만 먼저 보면 됩니다.

1. [프로젝트 시작 동기](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/project-motivation.md)
2. [문제 정의](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/problem.md)
3. [MVP](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp.md)
4. [MVP Decisions](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-decisions.md)
5. [MVP Implementation Outline](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-implementation-outline.md)

### 구현 문서

구현 상세나 로컬 검증 기준이 궁금하다면 아래 문서를 보면 됩니다.

- [Backend Implementation Guide](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/backend-implementation-guide.md)
- [Frontend Implementation Guide](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/frontend-implementation-guide.md)
- [Backend Quickstart](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/backend-quickstart.md)
- [Tech Stack Decision](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/tech-stack-decision.md)

### 참고 문서

세부 이슈 검토나 보강 개념 문서는 아래에 따로 둡니다.

- [Issue #10 Review: 폐기 수량 0 상황 처리 정책 정의](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/issue-10-no-discard-flow.md)
- [Issue #6 Review: 폐기 이력 저장 범위 재검토](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/issue-6-discard-history-review.md)
- [MVP DB Concept](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-db-concept.md)
