# Store-Expiration-Tracker

편의점에서 상품별 소비기한 상태를 끊기지 않게 추적하기 위한 프로젝트입니다.

이 저장소는 문제 정의, MVP 설계, 그리고 로컬 검증용 구현 기준을 함께 정리하고 있습니다. 목표는 전체 재고 관리 시스템을 만드는 것이 아니라, 한 번 등록한 상품이 소비기한 값이 있든 없든 추적 대상에서 사라지지 않도록 하는 것입니다.

## 왜 필요한가

기존 POS에도 소비기한 등록 기능은 있지만, 실제 운영에서는 상품별 현재 상태를 계속 유지하기 어렵습니다.

특히 다음에 등록할 소비기한이 없는 상태에서 품목을 삭제하면, 소비기한 정보뿐 아니라 그 상품이 다시 확인이 필요한 대상이라는 사실도 함께 사라집니다. 그 결과 근무자는 "내가 어떤 상품을 지웠지?", "어떤 상품을 다시 확인해야 하지?"를 기억에 의존하게 됩니다. 이 프로젝트는 그 인지 소모를 줄이기 위한 도구를 만드는 데 초점을 둡니다.

## 현재 범위

현재 MVP에서 다루는 범위는 아래와 같습니다.

- 상품별 현재 소비기한 상태 추적
- 오늘 확인이 필요한 소비기한 있는 상품과 `NULL` 상품의 분리 조회
- 바코드 기반 소비기한 등록 흐름과 필요 시 신규 상품 등록
- 폐기 처리 후 다음 소비기한 반영
- 상품 아카이빙과 재활성화
- 폐기 데이터 누적 저장

다음 항목은 현재 범위에 포함하지 않습니다.

- 편의점 전체 재고 관리
- 발주 기능
- 매출 및 판매 분석 기능
- 복잡한 분석 대시보드

## 현재 상태

현재는 Vue 기반 프론트엔드와 FastAPI 백엔드 구현 기준을 정리했고, 이를 바탕으로 로컬 검증용 MVP를 만드는 단계입니다.

핵심 방향은 `상단 상품 등록 + 메인 처리 대상 + 우측 미확인 사이드바` 구조의 운영 화면을 먼저 만들고, 이후 폐기 데이터를 바탕으로 발주 판단에 참고할 수 있는 구조로 확장하는 것입니다.

현재 프론트엔드 소스는 `frontend/`, 백엔드 소스는 `app/`에 있습니다.

## 문서

권장 읽기 순서는 아래와 같습니다.

1. [프로젝트 시작 동기](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/project-motivation.md)
2. [문제 정의](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/problem.md)
3. [MVP](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp.md)
4. [MVP Decisions](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-decisions.md)
5. [MVP Implementation Outline](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-implementation-outline.md)
6. [Backend Implementation Guide](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/backend-implementation-guide.md)
7. [Frontend V1 Implementation](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/frontend-v1-implementation.md)
8. [Tech Stack Decision](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/tech-stack-decision.md)
9. [Backend Quickstart](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/backend-quickstart.md)
