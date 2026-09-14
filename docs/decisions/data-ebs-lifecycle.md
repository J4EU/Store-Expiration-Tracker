# Data EBS Lifecycle

## 현재 선택

SQLite 서비스 데이터는 EC2 Root EBS가 아니라 별도 Data EBS에 둔다. Data EBS는 별도 Terraform state에서 보존하고, EC2 layer는 기존 볼륨을 attachment로만 연결한다.

Root EBS는 EC2 종료 시 함께 삭제되는 실행 환경으로 유지한다. 평시 EC2를 멈출 때는 stop/start를 사용하며, EC2 교체가 필요하면 같은 Data EBS를 새 EC2에 다시 연결하는 경계를 둔다.

다만 장애나 침해 사고가 의심되면 Root EBS에 남은 로그, 마지막 실행 상태, 설정 변경, 침해 흔적의 조사 가치를 먼저 판단한다. 보존이 필요하면 정상 폐기 전에 snapshot 등의 방법으로 남길 수 있으며, 이는 일반적인 backup 정책과는 별개의 예외다.

## 선택 이유

local Compose named volume은 컨테이너 lifecycle과 SQLite 데이터를 분리하지만, EC2 또는 Root EBS 교체 뒤의 데이터 보존 경계는 제공하지 않는다.

Data EBS를 분리하면 OS, Docker, application checkout처럼 재구성 가능한 실행 환경과 SQLite 서비스 데이터를 다른 lifecycle로 다룰 수 있다. EC2를 교체해야 할 때도 기존 Data EBS가 정상이라면 같은 데이터를 새 EC2에서 계속 사용할 수 있다.

## 수용한 trade-off

- Data EBS state, attachment, mount, Compose bind mount를 함께 관리해야 한다.
- EC2 replacement 뒤에도 실행 환경 자체는 다시 준비해야 한다.
- Data EBS 분리는 backup이나 snapshot이 아니며, 운영자 실수, 애플리케이션 버그, filesystem 손상, 침해 사고에 대한 과거 시점 복원을 제공하지 않는다.
- backup, snapshot, restore 전략은 현재 결정과 구현 범위에 포함하지 않는다.

현재 filesystem 초기화와 mount 자동화의 동작은 Architecture 문서와 `infra/` 구현을 따른다. 이 문서는 그 절차를 복제하지 않는다.

## 재검토 조건

- SQLite 데이터 규모나 동시성 요구가 현재 저장 구조의 경계를 넘을 때
- backup, snapshot, restore 목표와 복구 시간 요구가 구체화될 때
- 여러 host나 관리형 데이터 저장소로 책임 경계를 바꿔야 할 때

## References

- [Issue #44](https://github.com/J4EU/Store-Expiration-Tracker/issues/44)
- [Issue #46](https://github.com/J4EU/Store-Expiration-Tracker/issues/46)
- [Issue #47](https://github.com/J4EU/Store-Expiration-Tracker/issues/47)
- [PR #49](https://github.com/J4EU/Store-Expiration-Tracker/pull/49)
