# Project Workflow

이 문서는 저장소 작업 방식에서 반복적으로 참고할 운영 기준을 짧게 기록한다.

## Main 보호 정책

2026-07-30부터 `main` 브랜치에 `Protect main` ruleset을 적용한다.

현재 기준은 아래와 같다.

- `main` 브랜치에는 직접 push하지 않고 PR을 통해 병합한다.
- `main` 브랜치 삭제와 non-fast-forward push를 허용하지 않는다.
- PR 병합 방식은 merge commit과 squash merge를 허용한다.
- rebase merge는 현재 허용하지 않는다.
- 필수 승인 리뷰 수는 두지 않지만, 열린 review thread는 병합 전에 해결한다.
- 로컬에서 실수로 `main`에 커밋한 경우, 해당 커밋을 작업 브랜치로 옮겨 PR을 만든다.

## Merge 방식

`main` 병합은 squash merge를 기본 전략으로 사용한다.

2026-07-30부터 squash merge를 기본 전략으로 시험했고, 2026-10-03에 기본 전략으로 확정했다. (#63)

- `main` 히스토리를 PR 단위로 읽기 쉽게 유지한다.
- PR 안의 중간 수정 커밋은 리뷰와 작업 맥락에 남기고, `main`에는 완료된 작업 단위를 남긴다.
- PR 안의 커밋 맥락을 `main`에 보존해야 할 때는 merge commit을 사용한다.

squash commit 제목은 저장소 설정(`COMMIT_OR_PR_TITLE`)이 채워 주는 기본값을 따른다.

- PR에 커밋이 1개면 그 커밋 제목을 쓴다.
- PR에 커밋이 2개 이상이면 PR 제목을 쓴다.
- 기본값은 병합할 때 사람이 직접 수정할 수 있다.
