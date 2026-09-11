# EC2 배포 인프라

이 디렉터리는 Store Expiration Tracker를 EC2에서 실행하기 위한 AWS 리소스를
Terraform으로 관리한다. 현재 구성은 실행 환경을 담는 EC2 레이어와 SQLite 데이터를
보관하는 Data EBS 레이어의 state를 분리한다.

EC2 내부의 Docker 설치와 애플리케이션 배포는 운영자가 직접 수행한다. Data EBS의
파일시스템 생성과 마운트는 EC2 `user_data`가 담당한다. Terraform은 AWS 리소스 관계와
최초 부팅 시 저장소 준비를 관리한다.

`user_data` 원문은 [scripts/prepare-data-ebs.sh](scripts/prepare-data-ebs.sh)에 두고,
Terraform은 이를 그대로 EC2에 전달한다.

## 구성

- default VPC의 default subnet에 Amazon Linux 2023 `t3.micro` EC2 1대
- `allowed_operator_cidr`에만 SSH(`22`)와 Nginx(`8080`)를 허용하는 보안 그룹
- `data-ebs` 레이어에서 생성하는 20GB `gp3` Data EBS 1개

| 구분 | 저장 대상 | 수명 주기 |
| --- | --- | --- |
| Root EBS | OS, Docker, 애플리케이션 | EC2 종료 시 함께 삭제 |
| Data EBS | SQLite 서비스 데이터 | EC2와 분리해 보존 |

Root EBS는 `delete_on_termination = true`를 유지한다. Data EBS는
`data-ebs`의 별도 state에서 `prevent_destroy`로 관리하고, 이 디렉터리는 Data EBS를
조회해 EC2에 attachment만 만든다. Data EBS의 Availability Zone과 같은 default subnet을
선택하므로 EC2와 Data EBS는 연결 가능한 AZ에 생성된다.

이 구성이 선택된 이유와 데이터 보존·복구·복원의 구분은
[Issue #44 Decision: EC2 / EBS 수명주기](../docs/deployment/issue-44-ec2-ebs-lifecycle-decision.md)에
정리한다.

## 적용 준비

Data EBS를 먼저 만들고, 출력된 볼륨 ID를 EC2 레이어의 변수로 전달한다.

```bash
cd data-ebs
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

`data_volume_id` 출력값을 확인한 뒤, 상위 디렉터리의
`terraform.tfvars.example`을 복사해 현재 공인 IPv4 주소와 그 ID를 입력한다.

```bash
cd ..
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars`는 Git에 포함하지 않는다. SSH에 사용할 기존 키 페어는
`key_pair_name`으로 지정하며, 기본값은 `j4eu-ec2`다.

기존 단일 state에서 Data EBS를 이미 만들었다면 새 Data EBS를 만들지 않는다.
먼저 `data-ebs/terraform.tfvars.example`을 `data-ebs/terraform.tfvars`로 복사하고
Data EBS의 Availability Zone을 입력한다. `data-ebs`를 초기화한 다음, 아래처럼
해당 리소스의 state만 이동한다.

```bash
terraform -chdir=data-ebs init
terraform state mv \
  -state-out=data-ebs/terraform.tfstate \
  aws_ebs_volume.sqlite_data \
  aws_ebs_volume.sqlite_data
```

이동 뒤 `data-ebs`에서 `terraform plan`을 실행해 Data EBS의 재생성이 없음을
확인하고, 상위 `infra`에서는 기존 attachment를 유지한 채 `terraform plan`을 실행한다.

## Terraform 실행

```bash
terraform init
terraform plan
terraform apply
```

apply 뒤에는 `public_ip`로 EC2에 접속하고, `data_volume_id`가 Data EBS 레이어의
출력과 같은지 확인한다.

## Data EBS와 Compose 연결

EC2 최초 부팅 시 `/dev/sdf`로 연결된 Data EBS가 나타날 때까지 기다린다. 파일시스템이
없는 새 볼륨이면 XFS를 만들고, 이미 파일시스템이 있으면 `mkfs` 없이 기존 타입을
사용한다. 인식할 수 없는 디스크 서명은 포맷하지 않고 초기화를 실패시킨다.

파일시스템 UUID를 `/etc/fstab`에 `nofail` 옵션으로 기록한 뒤
`/srv/store-expiration-tracker/data`에 마운트한다. 따라서 EC2를 교체해 NVMe 장치명이
달라져도 같은 Data EBS를 자동으로 연결할 수 있다.

그 뒤 EC2에서는 기본 Compose 파일과 전용 오버라이드를 함께 사용한다.

```bash
docker compose -f compose.yaml -f compose.ec2.yaml up --build -d
```

[compose.ec2.yaml](../compose.ec2.yaml)은 backend의 `/app/data`를 Data EBS의
`/srv/store-expiration-tracker/data`에 bind mount한다. 로컬 Compose의
`sqlite_data` named volume 구성은 이 파일을 사용하지 않으므로 바뀌지 않는다.

## 수명 주기 운영

평시에는 EC2를 stop/start한다. start 시 `/etc/fstab`에 기록된 UUID를 이용해 Data EBS가
자동으로 마운트되며, 이후 Compose를 실행한다.

EC2를 교체하면 Terraform이 같은 Data EBS를 새 EC2에 연결한다. 새 EC2의 최초 부팅
자동화가 기존 파일시스템을 확인하고 같은 경로에 마운트한 뒤 Compose를 실행한다.

## Data EBS 자동화 검증

새 Data EBS로 처음 생성한 EC2에서 아래 명령으로 mount와 UUID를 확인한다.

```bash
findmnt /srv/store-expiration-tracker/data
lsblk -f
sudo blkid /dev/sdf
grep '/srv/store-expiration-tracker/data' /etc/fstab
```

이후 해당 경로에 sentinel 파일을 만들고 UUID를 기록한다. EC2 레이어만 destroy/apply해
같은 `data_volume_id`로 새 EC2를 만든 뒤, 아래 조건을 다시 확인한다.

```bash
findmnt /srv/store-expiration-tracker/data
sudo blkid -s UUID -o value /dev/sdf
sudo test -f /srv/store-expiration-tracker/data/ebs-recreate-check
sudo tail -n 100 /var/log/cloud-init-output.log
```

기존 UUID와 sentinel 파일이 유지되고 새 EC2에서 mount됐으면 기존 Data EBS를
재포맷하지 않고 재연결한 것이다. `infra/data-ebs` 레이어는 이 검증에서 destroy하지
않는다.

EC2 레이어에서 `terraform destroy`를 실행하면 attachment, EC2, 보안 그룹만 삭제된다.
Data EBS는 별도 `data-ebs` state에 있으므로 남는다. Data EBS를 폐기해야 할 때만
`data-ebs` 레이어의 보호 설정을 검토한 뒤 별도로 정리한다.

## 관련 기록

- [EC2 Compose 검증 스파이크](compose-spike.md): Data EBS 분리 이전에 수행한
  EC2 Compose 실행 관찰 기록
