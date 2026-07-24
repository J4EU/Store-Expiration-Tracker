# Store-Expiration-Tracker

편의점에서 상품별 소비기한 상태를 끊기지 않게 추적하기 위한 프로젝트입니다.

이 저장소는 실제 현장에서 겪은 소비기한 관리 문제를 바탕으로, 로컬에서 바로 검증 가능한 추적 도구를 만든 과정을 다룹니다. 현재는 FastAPI 백엔드와 Vue 프론트엔드로 MVP를 구현해 두었고, 다음 단계로 배포 가능한 형태로 다듬고 있습니다.

## 지금 할 수 있는 것

- 바코드 기준으로 상품을 조회하고, 없을 때만 신규 등록
- 상품별 현재 소비기한 상태 추적
- `expiration_date = NULL`도 정상적인 `미확인` 상태로 유지
- `오늘 처리`와 `미확인` 흐름을 같은 운영 화면에서 관리
- `폐기 완료`와 `폐기 없음`을 구분해 다음 상태 반영
- 상품 아카이빙과 복구
- 폐기 이력 누적 저장

## 대표 흐름

현재 MVP를 가장 잘 설명하는 기본 흐름은 아래와 같습니다.

1. `등록 시작`
2. `바코드 조회`
3. 기존 상품이면 소비기한만 반영하고, 없으면 신규 등록
4. 메인 화면에서 `오늘 처리` 대상과 `미확인` 대상을 함께 관리
5. 필요 시 `폐기 완료`, `폐기 없음`, `아카이브` 처리

현재 운영 화면의 핵심 구조는 `좌측 사이드 패널 + 메인 영역` 입니다.

- 좌측 사이드 패널: 등록 시작 버튼, `오늘 처리 / 미확인` 수량, 미확인 목록
- 메인 영역: `오늘 처리 / 전체` 필터, 처리 대상 리스트, 아카이브 조회 전환

## 빠른 실행

### 백엔드

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ADMIN_PASSWORD='change-this-password'
export SESSION_SECRET='change-this-session-secret'
uvicorn app.main:app --reload
```

- API 문서: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- DB 파일: `data/store_expiration_tracker.db`

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

- 개발 서버: [http://127.0.0.1:5173](http://127.0.0.1:5173)

처음 확인할 때는 `등록 시작 -> 바코드 조회 -> 소비기한 반영 -> 오늘 처리/미확인 확인` 순서로 보면 됩니다.

## 왜 필요한가

기존 POS에도 소비기한 등록 기능은 있지만, 실제 운영에서는 상품별 현재 상태를 계속 유지하기 어렵습니다.

특히 다음에 등록할 소비기한이 없는 상태에서 품목을 삭제하면, 소비기한 정보뿐 아니라 그 상품이 다시 확인이 필요한 대상이라는 사실도 함께 사라집니다. 그 결과 근무자는 "내가 어떤 상품을 지웠지?", "어떤 상품을 다시 확인해야 하지?"를 기억에 의존하게 됩니다. 이 프로젝트는 그 인지 소모를 줄이기 위한 도구를 만드는 데 초점을 둡니다.

핵심은 단순히 소비기한 날짜를 저장하는 것이 아니라, 한 번 관리 대상으로 올린 상품이 지금 `확인됨` 상태인지 `미확인` 상태인지가 시스템에 계속 남아 있도록 만드는 것입니다.

초기 가정에서 출발해 실제 등록 작업 후 방향을 어떻게 조정했는지는 [프로젝트 시작 동기](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/project-motivation.md), [MVP 방향 전환](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-pivot.md), [MVP Decisions](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-decisions.md)에서 나눠 정리합니다.

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
- 현재 운영 기준은 `단일 점포 / 단일 운영자`를 전제로 한다
- 공개 회원가입 없이, 미리 생성한 운영자 계정으로만 로그인하는 접근 제어를 둔다

다음 항목은 현재 범위에 포함하지 않습니다.

- 편의점 전체 재고 관리
- 발주 기능
- 매출 및 판매 분석 기능
- 복잡한 분석 대시보드
- 멀티 점포 데이터 모델
- 공개 회원가입 기능

## 현재 상태

현재는 Vue 기반 프론트엔드와 FastAPI 백엔드로 로컬 검증 가능한 MVP를 구현해 두었고, 운영 API 접근 제어의 1차 뼈대와 프론트 로그인 연결까지 반영해 둔 상태입니다.

- 프론트엔드 소스: `frontend/`
- 백엔드 소스: `app/`
- 현재 로컬 DB: `data/store_expiration_tracker.db`

이후에는 누적된 폐기 데이터를 바탕으로 발주 판단에 참고할 수 있는 구조와, 실제 배포 가능한 운영 형태로 확장하는 방향을 염두에 두고 있습니다.

현재 접근 제어 기준은 아래와 같습니다.

- `GET /health`를 제외한 운영 화면/API는 로그인 뒤에 둔다.
- 공개 회원가입은 열지 않는다.
- 운영자 계정은 초기 seed 또는 직접 주입으로 생성한다.
- `ADMIN_PASSWORD`, `SESSION_SECRET` 환경변수는 서버 시작 전에 반드시 주입해야 한다.
- 초기 세션 정책은 로그인 시점부터 최대 `4시간` 동안만 유효한 고정 만료를 둔다.
- 인증 쿠키는 영구 저장하지 않는 세션 쿠키를 둔다.
- 브라우저 종료는 세션을 끝낼 수 있는 추가 조건으로 보되, 보안 기준 자체는 `4시간` 고정 만료에 둔다.
- 무활동 시간 기준 자동 로그아웃은 1차에서는 보류한다.
- 세션 만료 후 재진입 UX는 추후 개선 항목으로 남겨 둔다.
- 인증 엔드포인트는 `login / logout / session 확인`의 최소 범위로 둔다.
- 멀티 점포는 현재 스키마 범위에 넣지 않고, 추후 확장 가능성으로만 남겨 둔다.

## 문서

### 핵심 문서

처음 읽는 사람이라면 아래 문서만 먼저 보면 됩니다.

1. [프로젝트 시작 동기](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/project-motivation.md)
2. [문제 정의](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/problem.md)
3. [초기 MVP](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp.md)
4. [MVP 방향 전환](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-pivot.md)
5. [MVP Decisions](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-decisions.md)
6. [MVP Implementation Outline](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-implementation-outline.md)

### 구현 문서

구현 상세나 로컬 검증 기준이 궁금하다면 아래 문서를 보면 됩니다.

- [Backend Quickstart](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/backend-quickstart.md)
- [Backend Implementation Guide](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/backend-implementation-guide.md)
- [Frontend Implementation Guide](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/frontend-implementation-guide.md)
- [Tech Stack Decision](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/tech-stack-decision.md)

### 참고 문서

세부 이슈 검토나 보강 개념 문서는 아래에 따로 둡니다.

- [MVP DB Concept](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/mvp-db-concept.md)
- [Issue #6 Review: 폐기 이력 저장 범위 재검토](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/issue-6-discard-history-review.md)
- [Issue #10 Review: 폐기 수량 0 상황 처리 정책 정의](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/issue-10-no-discard-flow.md)
- [Issue #20 Review: 배포용 인증/세션 설정 정리](https://github.com/J4EU/Store-Expiration-Tracker/blob/main/docs/issue-20-deployment-auth-session-policy.md)
