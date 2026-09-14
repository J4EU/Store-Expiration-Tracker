# Decisions

이 디렉터리는 현재도 유효한 중요한 결정과 그 이유, 수용한 trade-off, 재검토 조건을 기록한다. Issue와 PR은 결정이 만들어진 작업 과정과 증거를 확인하는 곳이고, 이 디렉터리는 현재 적용되는 결론을 찾는 곳이다.

## 어떤 질문을 갖고 왔는가?

| 질문 | 문서 |
| --- | --- |
| 왜 FastAPI와 Vue를 선택했는가? 다른 스택으로 바꿔야 하는 조건은 무엇인가? | [Technology Stack](technology-stack.md) |
| 왜 운영자 session을 현재 방식으로 관리하는가? | [Operator Session Policy](operator-session-policy.md) |
| 왜 외부 API 경계를 same-origin `/api`로 통일했는가? | [Same-Origin API Boundary](same-origin-api-boundary.md) |
| 어떤 경로와 값이 외부 공개·secret handling의 대상인가? | [Public Surface and Secret Handling](public-surface-and-secret-handling.md) |
| 왜 EC2와 SQLite data lifecycle을 분리했는가? | [Data EBS Lifecycle](data-ebs-lifecycle.md) |
| 왜 상품을 삭제하지 않고 보존하며, 아카이브를 운영자가 직접 결정하는가? | [Product Retention and Archiving](product-retention-and-archiving.md) |
| 무엇을 실제 폐기 이력으로 저장하며, 왜 그 범위만 저장하는가? | [Discard History Scope](discard-history-scope.md) |

문서가 늘어나면 파일 개수 대신 이 질문 기반 탐색표를 먼저 확장한다. 아직은 하위 디렉터리를 만들지 않는다.
