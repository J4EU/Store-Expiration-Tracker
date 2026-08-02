# 프로젝트 문서 역할 조사

## 목적

이 문서는 GitHub Issue #37에서 조사한 `docs/` 문서의 역할과 관계를 기록한다.

목적은 문서를 전면 개편하거나 단일 Source of Truth를 정하는 것이 아니다. 이후 문서를 수정할 때 어떤 문서를 먼저 확인하고, 어떤 개선을 별도 작업으로 분리할지 판단할 수 있는 현재 상태의 근거를 남기는 것이다.

조사 기준일은 2026-08-03이며, `docs/README.md`를 포함한 `docs/`의 Markdown 문서 22개를 대상으로 했다. 코드·실제 배포 환경·외부 GitHub Issue 본문의 최신 사실 여부는 이번 조사 대상이 아니다.

## 역할 정의

| 역할 | 의미 |
| --- | --- |
| 기준 문서 | 현재 적용하는 규칙, 정책, 범위 또는 설계 기준을 설명한다. |
| 실행 문서 | 작업 절차, 실행 명령, 확인 순서처럼 실제 수행 방법을 설명한다. |
| 기록 문서 | 특정 시점의 문제, 판단 과정, 결정 이유, 변경 이력을 보존한다. |
| 안내 문서 | 관련 문서를 연결하고 탐색 경로를 제공한다. |

여기서 주 역할은 해당 문서를 처음 열어야 하는 가장 주된 이유다. 주 역할이 기준이라고 해서 유일한 기준 문서이거나, 기록이라고 해서 현재 규칙을 전혀 담지 않는다는 뜻은 아니다.

## 문서별 주 역할

| 문서 | 주 역할 | 함께 가진 역할 또는 관찰 |
| --- | --- | --- |
| `docs/README.md` | 안내 | 주제별 목록과 진입점을 제공한다. |
| `product/project-motivation.md` | 기록 | 프로젝트를 시작한 현장 경험과 문제의식을 보존한다. |
| `product/problem.md` | 기준 | 현재 해결하려는 업무 문제와 제약을 설명한다. |
| `product/mvp.md` | 기준 | MVP 범위, 핵심 흐름, 우선순위를 설명한다. |
| `product/mvp-pivot.md` | 기록 | 실제 사용 뒤 MVP 가정이 바뀐 경위를 보존한다. |
| `product/mvp-decisions.md` | 기준 | 방향 전환 뒤 확정한 제품·데이터·화면 규칙을 모은다. 결정 이유도 함께 있어 기록 역할이 섞인다. |
| `product/mvp-db-concept.md` | 기준 | 현재 MVP 데이터 구조를 빠르게 확인하는 개념 기준이다. 초기 개념 메모라는 성격도 남아 있다. |
| `product/issue-6-discard-history-review.md` | 기록 | Issue #6의 재검토 과정과 결론을 보존한다. `discard_histories` 규칙도 함께 고정한다. |
| `product/issue-10-no-discard-flow.md` | 기록 | Issue #10의 문제와 재검토 결론을 보존한다. 폐기 없음 처리 규칙도 함께 고정한다. |
| `development/backend-quickstart.md` | 실행 | 백엔드·프론트 로컬 실행과 빠른 확인 순서를 제공한다. API 예시와 현재 동작 설명도 포함한다. |
| `development/backend-implementation-guide.md` | 기준 | 데이터 모델, 상태 전이, 대시보드 조회, API·인증 범위를 설명한다. 구현 안내 성격이 일부 섞인다. |
| `development/frontend-implementation-guide.md` | 기준 | 화면 구조, 입력·조회 규칙, 프론트 구현 범위를 설명한다. 구현 우선순위도 포함한다. |
| `development/mvp-implementation-outline.md` | 기준 | MVP를 구현 규칙·DB 초안·대시보드 기준으로 풀어낸다. 설계 초안의 기록 성격도 있다. |
| `development/tech-stack-decision.md` | 기록 | 초기 기술 선택의 후보와 판단 이유를 보존한다. 현재 스택을 다시 확인하는 기준 역할도 일부 가진다. |
| `deployment/issue-20-deployment-auth-session-policy.md` | 기록 | Issue #20의 인증·세션 검토와 결정 이유를 보존한다. 현재 쿠키·세션 기준이 함께 있다. |
| `deployment/issue-21-env-config-separation.md` | 기록 | Issue #21의 환경 분리 판단과 후속 반영 현황을 보존한다. same origin, `/api`, 환경변수 기준이 함께 있다. |
| `deployment/issue-22-public-scope-secret-operations.md` | 기록 | Issue #22의 공개 범위·secret 운영 판단과 후속 반영 현황을 보존한다. 현재 공개·secret 기준이 함께 있다. |
| `deployment/issue-23-pre-deploy-auth-checklist.md` | 기록 | Issue #23의 검증 항목과 선행 기준을 보존한다. 체크리스트 성격은 있지만 상세 실행은 Runbook에 넘긴다. |
| `deployment/pre-deploy-auth-runbook.md` | 실행 | 실제 배포 URL에서 설정·경로·로그인·쿠키를 확인하는 순서와 기록 양식을 제공한다. |
| `deployment/issue-28-spa-fallback-routing-policy.md` | 기록 | Issue #28에서 확인한 현상과 URL 정책의 판단 배경을 보존한다. 현재 API·fallback URL 규칙도 함께 있다. |
| `process/project-workflow.md` | 기준 | main 보호와 병합 방식의 현재 저장소 작업 기준을 짧게 제공한다. |

## 역할 혼합 문서와 분리 필요성

아래 문서는 기록의 맥락과 현재 기준을 함께 담는다. 이는 현재로서는 판단 이유를 보존하는 장점이 있지만, 규칙만 빨리 찾으려는 독자에게는 탐색 비용이 된다.

| 문서군 | 섞인 역할 | 이번 조사에서의 판단 |
| --- | --- | --- |
| `product/mvp-decisions.md`, `product/mvp-db-concept.md`, `development/mvp-implementation-outline.md` | 기준 + 기록 | 현재 제품·데이터 규칙과 결정/초안의 맥락이 함께 있다. 즉시 분리하지 않고, 중복 규칙을 먼저 비교할 후보로 남긴다. |
| `product/issue-6-discard-history-review.md`, `product/issue-10-no-discard-flow.md` | 기록 + 기준 | Issue Review는 결정 과정 보존이 주 역할이다. 현재 규칙이 바뀔 때는 제품 기준 문서에도 반영됐는지 함께 확인할 필요가 있다. |
| `deployment/issue-20-deployment-auth-session-policy.md`부터 `issue-23-pre-deploy-auth-checklist.md` 및 `issue-28-spa-fallback-routing-policy.md` | 기록 + 기준 또는 실행 | Issue별 검토 기록 안에 production 정책·검증 기준이 남아 있다. 정책과 검증 절차를 찾을 때 Issue 번호를 알아야 하는 구조다. |
| `development/backend-quickstart.md`, `backend-implementation-guide.md`, `frontend-implementation-guide.md` | 실행 + 기준 | 실행 절차와 현재 구현/설계 설명이 같은 문서에 일부 공존한다. 빠른 실행 경로와 설계 기준을 분리할 필요가 있는지 후속으로 검토한다. |

이번 이슈에서는 역할 혼합을 문서 이동·분할의 근거로만 기록한다. 어느 문서를 분리하거나 어떤 문서를 기준 문서로 승격할지는 결정하지 않는다.

## 규칙 중복 후보

아래는 같은 규칙 또는 동일한 판단 영역이 둘 이상 문서에서 설명되는 후보다. 내용 충돌 여부나 어느 문서가 우선인지까지는 이번 조사에서 판정하지 않았다.

| 규칙 또는 판단 영역 | 함께 확인할 문서 | 관찰 |
| --- | --- | --- |
| 제품 문제와 지속 추적 필요성 | `product/project-motivation.md`, `product/problem.md`, `product/mvp.md`, `product/mvp-pivot.md` | 시작 동기, 현장 문제, MVP 원칙, 방향 전환에 같은 배경이 반복된다. |
| 상품 보존, 아카이빙, 소비기한 상태와 폐기 흐름 | `product/mvp.md`, `product/mvp-decisions.md`, `product/mvp-db-concept.md`, `development/mvp-implementation-outline.md`, `development/backend-implementation-guide.md` | 제품 정책에서 DB·상태 전이·API 규칙으로 반복된다. 변경 시 영향을 함께 확인해야 한다. |
| 대시보드 처리 대상과 미확인 대상 기준 | `product/mvp.md`, `product/mvp-decisions.md`, `development/mvp-implementation-outline.md`, `development/backend-implementation-guide.md`, `development/frontend-implementation-guide.md` | 제품·백엔드 조회·프론트 화면에서 같은 필터와 표시 기준을 설명한다. |
| 폐기 이력과 `폐기 없음` 처리 | `product/mvp-decisions.md`, `product/issue-6-discard-history-review.md`, `product/issue-10-no-discard-flow.md`, `development/backend-implementation-guide.md`, `development/backend-quickstart.md` | Issue Review의 결론이 제품·API 설명에도 걸쳐 있다. |
| 로컬 `/api` proxy와 API 접근 방식 | `development/backend-quickstart.md`, `development/frontend-implementation-guide.md`, `deployment/issue-21-env-config-separation.md`, `deployment/issue-28-spa-fallback-routing-policy.md` | 로컬 실행 방식, 환경 경계, fallback URL 정책이 각각 설명된다. |
| production 인증·세션·쿠키 기준 | `deployment/issue-20-deployment-auth-session-policy.md`, `deployment/issue-21-env-config-separation.md`, `deployment/issue-23-pre-deploy-auth-checklist.md`, `deployment/pre-deploy-auth-runbook.md` | 정책·환경변수·검증 항목·실행 절차가 이어진다. |
| production 공개 범위와 secret 운영 | `deployment/issue-22-public-scope-secret-operations.md`, `deployment/issue-23-pre-deploy-auth-checklist.md`, `deployment/pre-deploy-auth-runbook.md` | 공개 경로와 비밀값 기준이 검증 문서에도 반복된다. |

## 문서 간 참조 후보

현재 Markdown 링크는 `docs/README.md`의 목록과 일부 Product 문서에 집중되어 있다. 아래 연결은 이번 조사에서 확인한 후보이며, 아직 추가하지 않았다.

| 시작 문서 | 연결 후보 | 이유 |
| --- | --- | --- |
| `docs/README.md` | 이 문서 | 역할 조사 결과의 탐색 진입점을 제공한다. |
| `product/project-motivation.md` | `product/problem.md` | 시작 동기에서 현재 문제 정의로 자연스럽게 이동할 수 있다. |
| `product/mvp.md` | `product/mvp-decisions.md`, `development/mvp-implementation-outline.md` | MVP 범위에서 확정 결정과 구현 규칙으로 이어진다. |
| `product/mvp-decisions.md` | `product/mvp-db-concept.md`, Issue #6·#10 Review | 데이터·폐기 관련 결론의 상세 근거를 따라갈 수 있다. |
| `development/backend-implementation-guide.md`, `development/frontend-implementation-guide.md` | `product/mvp-decisions.md`, `development/mvp-implementation-outline.md` | 구현 기준의 제품 결정·공통 상태 규칙을 추적할 수 있다. |
| `development/backend-quickstart.md` | `deployment/issue-21-env-config-separation.md`, `deployment/issue-28-spa-fallback-routing-policy.md` | 로컬 실행의 환경변수와 `/api` 경로 배경을 확인할 수 있다. |
| `deployment/issue-20-deployment-auth-session-policy.md` | Issue #21·#22 Review | 인증·세션 정책에서 환경 경계와 공개/secret 운영 기준으로 이어진다. |
| `deployment/issue-21-env-config-separation.md`, `issue-22-public-scope-secret-operations.md` | `issue-23-pre-deploy-auth-checklist.md`, `pre-deploy-auth-runbook.md` | 정책에서 검증 기준과 실행 절차로 이어진다. |
| `deployment/issue-23-pre-deploy-auth-checklist.md` | `pre-deploy-auth-runbook.md` | 체크리스트의 각 항목을 실제 수행 절차로 이어 준다. |
| `deployment/issue-28-spa-fallback-routing-policy.md` | `development/frontend-implementation-guide.md`, `deployment/pre-deploy-auth-runbook.md` | 로컬 URL 정책과 production reverse proxy 검증의 경계를 분명히 한다. |
| `process/project-workflow.md` | `.github/pull_request_template.md`, `AGENTS.md` | 작업 기준을 PR 작성 규칙과 저장소 지침으로 연결할 수 있다. 이들은 `docs/` 조사 대상 밖이다. |

## 후속 작업 후보

이번 이슈에서는 아래 항목을 구현하지 않는다.

1. 제품 정책·상태 전이·대시보드 규칙의 중복 문서가 실제로 같은 내용을 유지하는지 비교하고, 수정 시 함께 갱신할 문서를 정리한다.
2. Issue Review에 남은 현재 규칙을 별도 기준 문서로 모을지, 각 Review 문서에 명시적인 현재 기준 요약을 둘지 결정한다.
3. 위 참조 후보 중 필요한 링크를 추가하고, 기존 절대 GitHub 링크를 상대 링크로 통일할지 검토한다.
4. `backend-quickstart.md`의 실행 절차와 구현 가이드의 설계 설명을 분리할 필요가 있는지 검토한다.
5. 문서의 우선 기준, 담당자, 갱신 시점 같은 거버넌스 체계가 필요한지 별도 이슈에서 결정한다.

## 이번 조사에서 확인한 범위

- 문서별 주 역할은 모두 하나씩 기록했다.
- 역할 혼합, 규칙 중복, 문서 간 참조 후보를 기록했다.
- 실제 문서 본문 개편, 링크 추가, 문서 이동·삭제, 코드·배포 검증은 수행하지 않았다.
