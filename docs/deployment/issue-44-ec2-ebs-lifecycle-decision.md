# Issue #44 Decision: EC2 / EBS 수명주기

## 문서 목적

이 문서는 GitHub Issue `#44 EC2 SQLite 데이터 저장소 수명 주기 결정 및 구현`에서 확정한 EC2와 EBS의 책임 및 수명주기 기준을 남긴다.

이번 문서는 구현 완료나 운영 검증 결과를 기록하지 않는다. 선택한 방향과 그 이유를 고정하고, 이후 구현과 검증이 따라야 할 경계를 정한다.

## 전제

현재 로컬 Compose 경로에서는 `sqlite_data` Docker named volume을 backend의 `/app/data`에 마운트한다. 이 구성은 컨테이너 생명주기와 SQLite 데이터를 분리하지만, EC2 인스턴스 또는 root EBS 수명주기 변화 뒤의 데이터 보존을 확인한 것은 아니다.

현재 Terraform의 EC2 root EBS는 `delete_on_termination = true`다. 별도 Data EBS와 그 연결·복구 절차는 아직 구현하거나 검증하지 않았다.

## 결정

### 평시 운영은 EC2 start/stop을 사용한다

근무 종료를 `terraform destroy`와 동일시하지 않는다. 평시에는 EC2를 매일 재생성하지 않고, 서비스 종료 후 EC2를 stop한다. 다시 사용할 때는 EC2를 start한 뒤 서비스를 실행한다.

`destroy` 또는 terminate는 비용 절감을 위한 일상적인 종료가 아니라 자원의 수명 종료가 필요한 경우에 사용한다.

### Root EBS와 Data EBS를 분리한다

SQLite 서비스 데이터는 별도 Data EBS에 둔다.

| 구분     | 책임                                                        |
| -------- | ----------------------------------------------------------- |
| Root EBS | OS, Docker/runtime, 애플리케이션 등 재구성 가능한 실행 환경 |
| Data EBS | SQLite 서비스 데이터                                        |

분리의 목적은 단순히 데이터를 영속화하는 것이 아니라, 실행 환경과 서비스 데이터를 서로 다른 lifecycle 및 recovery unit으로 관리하는 데 있다. 실행 환경만 재구축해야 할 때 SQLite 데이터까지 같은 복구 단위에 묶지 않는다.

### Root EBS는 정상 폐기 시 함께 삭제한다

Root EBS에는 서비스의 핵심 영속 데이터를 저장하지 않는다. 따라서 정상적인 EC2 폐기에서는 `delete_on_termination = true`를 기본 정책으로 유지한다.

장애 또는 침해 사고에서는 기존 Root EBS에 로그, 마지막 실행 상태, 설정 변경, 원인 분석 또는 침해 흔적이 남아 있을 수 있다. 이 경우에는 폐기 전에 조사 목적의 보존 필요성을 판단하고, 필요하면 snapshot 등의 방법으로 명시적으로 보존한 뒤 정리한다.

### Data EBS 분리와 백업·복구를 구분한다

Data EBS를 분리해도 EC2 침해, 운영자 실수, 애플리케이션 버그, OS·파일시스템 문제, 잘못된 배포 또는 인프라 장애로부터 데이터의 신뢰성이 자동으로 보장되지는 않는다.

- Persistence: 정상 종료나 재시작 뒤 현재 데이터를 유지한다.
- Recovery: 현재 데이터가 원하는 상태가 아닐 때 과거의 신뢰 가능한 상태로 되돌린다.

Data EBS 분리는 Persistence와 실행 환경 분리를 위한 선택이다. Recovery를 위해서는 별도의 snapshot 또는 backup 정책과 restore 검증이 필요하다.

## 수용하는 비용

Data EBS 분리에 따라 EBS lifecycle 관리, EC2 attachment, filesystem·mount 관리, Docker의 SQLite 경로 연결, EC2 교체 뒤 재연결, snapshot·restore 절차를 관리해야 한다.

이 복잡성은 서비스 데이터와 실행 환경을 독립적으로 관리하고 복구 단위를 분리하는 가치를 위해 수용한다.

## 관련 문서

- [Issue #41 Review: 로컬 최소 배포 경로 구성 및 검증](issue-41-local-deployment-path.md)
