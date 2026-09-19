# Infrastructure and Data Lifecycle

이 문서는 현재 Terraform과 EC2 Compose override가 만드는 EC2와 SQLite 데이터의 lifecycle 경계를 설명한다. Terraform 실행 방법과 shell 구현 세부사항은 `infra/`와 [infra/README.md](../../infra/README.md)를 기준으로 확인한다.

## 책임 경계

현재 인프라는 두 Terraform state로 나뉜다.

```text
infra/data-ebs/
  -> SQLite Data EBS 생성과 보존
  -> data_volume_id
  -> infra/
       -> EC2, security group, 기존 Data EBS attachment
```

EC2의 Root EBS에는 OS, Docker, 애플리케이션처럼 재구성 가능한 실행 환경이 놓인다. Root EBS는 EC2 종료 시 함께 삭제되도록 구성돼 있다. SQLite 서비스 데이터는 별도 Data EBS에 둔다.

EC2 layer는 Data EBS를 새로 만들지 않고 `data_volume_id`로 기존 볼륨을 조회해 attachment만 관리한다. Data EBS layer는 별도 state와 `prevent_destroy`로 이 볼륨을 보존한다. EC2는 Data EBS와 같은 Availability Zone의 subnet에서 생성된다.

## Data EBS 준비와 연결

EC2 최초 부팅 시 user data는 attachment device를 기다린 뒤 파일시스템 상태를 확인한다.

- 파일시스템이 없는 새 볼륨만 XFS로 초기화한다.
- 이미 인식 가능한 파일시스템이 있으면 재포맷하지 않는다.
- 알 수 없는 디스크 signature는 포맷하지 않고 실패한다.
- filesystem UUID를 `/etc/fstab`에 기록하고, Data EBS를 `/srv/store-expiration-tracker/data`에 mount한다.

EC2용 Compose override는 이 host 경로를 backend의 `/app/data`에 bind mount한다. 따라서 backend가 사용하는 SQLite 경로는 local Compose와 같지만, EC2에서는 Data EBS가 그 데이터를 제공한다.

## EC2 교체 시 경계

EC2 layer를 교체해도 Data EBS가 보존되어 있고 같은 `data_volume_id`를 다시 전달하면, 새 EC2는 그 볼륨을 다시 attach하고 기존 filesystem을 유지한 채 mount하도록 구성돼 있다.

이 경계가 보존하려는 것은 Data EBS 안의 SQLite 데이터와 filesystem이다. EC2와 Root EBS에 있던 OS, Docker 설치 상태, application checkout, host 설정은 새 EC2에 남지 않는다. Data EBS가 보존된다고 애플리케이션 실행 환경 전체가 복구되는 것은 아니다.

## persistence, replacement survival, backup의 구분

- **Persistence**: 컨테이너 재시작이나 정상적인 서비스 재기동 뒤 SQLite 데이터를 유지하는 성질이다.
- **EC2 replacement survival**: 기존 Data EBS를 새 EC2에 다시 연결해, EC2 교체 뒤에도 그 EBS의 데이터를 계속 사용하는 성질이다.
- **Backup / snapshot**: 데이터가 손상되거나 잘못 변경됐을 때 신뢰할 수 있는 과거 상태로 되돌릴 별도 사본이다.

현재 Data EBS 분리는 앞의 두 경계를 제공하기 위한 구성이다. backup이나 snapshot 전략, 그리고 그것을 이용한 복원 절차는 현재 구현 범위에 포함하지 않는다.

## 현재 확인 범위

이 문서는 repository에 있는 Terraform, user data, Compose override가 의도한 구조를 설명한다. 특정 AWS resource가 지금 존재하는지, 또는 현재 운영 EC2에서 어떤 환경변수가 사용 중인지는 여기서 주장하지 않는다.

## Source of truth

- `infra/data-ebs/`
- `infra/main.tf`, `infra/variables.tf`, `infra/scripts/prepare-data-ebs.sh`
- `compose.ec2.yaml`
- `infra/README.md`
