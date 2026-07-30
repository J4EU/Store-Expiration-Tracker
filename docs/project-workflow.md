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

2026-07-30부터 `main` 병합 방식은 squash merge를 기본 전략으로 시험한다.

현재 의도는 아래와 같다.

- `main` 히스토리를 PR 단위로 읽기 쉽게 유지한다.
- PR 안의 중간 수정 커밋은 리뷰와 작업 맥락에 남기고, `main`에는 완료된 작업 단위를 남긴다.
- squash commit 제목은 PR 제목을 기준으로 한다.

다만 이 방식은 아직 최종 고정 정책이 아니다.

운영 경험에 따라 merge commit을 기본 전략으로 변경할 수 있으며, 병합 맥락을 보존해야 하는 PR에서는 예외적으로 merge commit을 사용할 수 있다.
