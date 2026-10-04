# EC2 Manual Deploy Runbook

이 문서는 새 EC2에서 Store Expiration Tracker를 실행하기까지의 현재 수동 배포 절차를 순서대로 기록한다. Terraform 레이어 구조와 Data EBS 자동화의 설명은 [EC2 배포 인프라](../../infra/README.md)를 따르고, 이 문서는 실행 순서와 명령만 다룬다.

## 전제와 범위

현재 절차는 아래 상태를 전제로 한다.

- 외부 진입점은 HTTP `http://<public_ip>:8080`이다. HTTPS와 443 구성은 없다.
- backend 환경변수는 EC2 checkout 안의 `deploy/prod/backend.env` 파일로 주입한다.
- 이미지는 EC2에서 직접 build한다. 이미지 registry는 쓰지 않는다.
- EC2를 start해도 컨테이너는 자동으로 시작되지 않는다.

이 문서가 다루지 않는 것:

- HTTPS 도입과 시크릿 주입 방식 고도화 ([Issue #65](https://github.com/J4EU/Store-Expiration-Tracker/issues/65))
- `data_volume_id` 수동 입력 제거 ([Issue #48](https://github.com/J4EU/Store-Expiration-Tracker/issues/48))
- 이미지 registry, 배포 자동화, 백업·복원

명령의 실행 위치는 각 단계 제목에 `[로컬]` 또는 `[EC2]`로 표시한다.

## 1. 사전 준비 [로컬]

- AWS 자격증명이 설정되어 있고 Terraform(`>= 1.15.0`)이 설치되어 있다.
- `ap-northeast-2`에 EC2 키 페어가 있고, 그 private key 파일을 로컬에 가지고 있다. 기본 키 페어 이름은 `j4eu-ec2`다.
- EC2에 접속할 네트워크에서 그 네트워크의 공인 IPv4를 확인할 수 있다.

## 2. 인프라 생성 [로컬]

저장소 최상위에서 시작한다.

### 2-1. Data EBS 준비

기존 Data EBS를 다시 쓰는 경우 새로 만들지 않는다. `data_volume_id`만 확인한다.

```bash
terraform -chdir=infra/data-ebs output data_volume_id
```

Data EBS가 아직 없을 때만 새로 만든다.

```bash
cp infra/data-ebs/terraform.tfvars.example infra/data-ebs/terraform.tfvars
# terraform.tfvars에 Availability Zone을 입력한다.
terraform -chdir=infra/data-ebs init
terraform -chdir=infra/data-ebs apply
terraform -chdir=infra/data-ebs output data_volume_id
```

### 2-2. EC2 생성

`infra/terraform.tfvars`가 없으면 예시 파일을 복사한다.

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

`infra/terraform.tfvars`에 아래 값을 입력한다.

- `allowed_operator_cidrs`: EC2에 접속할 네트워크의 공인 IPv4를 `/32`로 입력한다. 그 네트워크에서 아래 명령으로 확인한다.

  ```bash
  curl -s https://checkip.amazonaws.com
  ```

- `data_volume_id`: 2-1에서 확인한 값을 입력한다.

```bash
terraform -chdir=infra init
terraform -chdir=infra apply
terraform -chdir=infra output public_ip
```

## 3. SSH 접속과 Data EBS mount 확인 [EC2]

```bash
ssh -i <private_key_path> ec2-user@<public_ip>
```

최초 부팅의 user data가 Data EBS를 `/srv/store-expiration-tracker/data`에 mount한다. mount가 끝났는지 확인한다.

```bash
findmnt /srv/store-expiration-tracker/data
```

출력이 없으면 user data 로그를 확인한다. user data가 끝나기 전일 수 있으므로 잠시 기다린 뒤 다시 확인한다.

```bash
sudo tail -n 100 /var/log/cloud-init-output.log
```

## 4. Host 준비 [EC2]

### 4-1. Git과 Docker 설치

```bash
sudo dnf install -y git docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
exit
```

docker 그룹 권한을 반영하려고 SSH를 다시 접속한다.

### 4-2. Docker Compose와 Buildx 설치

Amazon Linux 2023 패키지 저장소에는 Docker Compose plugin과 Compose build에 필요한 Buildx가 없다. GitHub release 바이너리를 Docker CLI plugin 경로에 설치한다. 버전은 이 Runbook을 검증할 때 사용한 버전으로 고정한다.

```bash
COMPOSE_VERSION=v5.6.0
BUILDX_VERSION=v0.37.2

sudo mkdir -p /usr/local/lib/docker/cli-plugins

sudo curl -fsSL \
  "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose

sudo curl -fsSL \
  "https://github.com/docker/buildx/releases/download/${BUILDX_VERSION}/buildx-${BUILDX_VERSION}.linux-amd64" \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx

sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
  /usr/local/lib/docker/cli-plugins/docker-buildx
```

설치를 확인한다.

```bash
docker compose version
docker buildx version
```

## 5. 애플리케이션 checkout [EC2]

```bash
git clone https://github.com/J4EU/Store-Expiration-Tracker.git
cd Store-Expiration-Tracker
```

이후 `[EC2]` 명령은 이 checkout 최상위에서 실행한다.

## 6. env 파일 준비 [EC2]

```bash
cp deploy/prod/backend.env.example deploy/prod/backend.env
chmod 600 deploy/prod/backend.env
```

`deploy/prod/backend.env`의 placeholder를 바꾼다.

- `ADMIN_PASSWORD`: 운영자 로그인 비밀번호다. 계정 이름은 `admin`이다.
- `SESSION_SECRET`: session 서명 키다. 아래처럼 생성할 수 있다.

```bash
openssl rand -hex 32
```

secret 원문은 Git, 문서, 이슈, PR, 채팅에 남기지 않는다.

**HTTP 테스트 한정 예외:** 현재 EC2는 HTTP로만 열려 있다. `SESSION_COOKIE_SECURE=true`를 유지하면 브라우저가 HTTP에서 session cookie를 보내지 않아 로그인 뒤 요청이 `401`로 실패한다([EC2 Compose 검증 스파이크](../../infra/compose-spike.md)). EC2를 띄워 테스트할 때만 아래처럼 바꾼다.

```text
SESSION_COOKIE_SECURE=false
```

이 상태에서는 비밀번호와 session cookie가 네트워크에서 평문으로 오간다. 테스트용으로만 쓰고, 보안 그룹이 허용한 운영자 IP에서만 접속한다. HTTPS 도입은 [Issue #65](https://github.com/J4EU/Store-Expiration-Tracker/issues/65)에서 다룬다.

## 7. 실행 [EC2]

```bash
docker compose -f compose.ec2.yaml up --build --wait
```

이미지를 EC2에서 직접 build하므로 첫 실행은 시간이 걸린다. `--wait`는 detached mode로 실행하고, health check가 있는 backend는 `healthy`, health check가 없는 nginx는 `running` 상태가 될 때까지 기다린다.

## 8. 동작 확인

### [EC2]

```bash
docker compose -f compose.ec2.yaml ps
curl -s http://localhost:8080/api/health
```

- 두 서비스가 `running`이고 backend가 `healthy`다.
- health 응답이 `{"status":"ok"}`다.

### [로컬 브라우저]

1. `http://<public_ip>:8080`에 접속한다.
2. `admin`과 `ADMIN_PASSWORD`로 로그인한다.
3. 상품 하나를 등록하고 목록에 나타나는지 확인한다.

### [EC2]

SQLite 파일이 Data EBS에 만들어졌는지 확인한다.

```bash
sudo ls -l /srv/store-expiration-tracker/data
```

`store_expiration_tracker.db`가 있으면 배포가 끝난 것이다.

## 9. EC2 stop/start 후 재기동

EC2를 start해도 컨테이너는 자동으로 시작되지 않는다. Elastic IP가 없으므로 public IP도 바뀔 수 있다.

[로컬] 새 public IP를 확인한다. `terraform output`은 state를 갱신해야 새 IP를 보여 준다.

```bash
terraform -chdir=infra apply -refresh-only
terraform -chdir=infra output public_ip
```

[EC2] SSH로 접속해 mount를 확인한 뒤 실행한다.

```bash
findmnt /srv/store-expiration-tracker/data
cd Store-Expiration-Tracker
docker compose -f compose.ec2.yaml up --wait
```

이후 8단계로 확인한다. 기존 데이터가 그대로 보여야 한다.

## 10. 코드 변경 재배포 [EC2]

```bash
cd Store-Expiration-Tracker
git pull
docker compose -f compose.ec2.yaml up --build --wait
```

`deploy/prod/backend.env`는 Git이 추적하지 않으므로 `git pull`로 바뀌지 않는다. `backend.env.example`에 새 변수가 추가됐다면 직접 반영한다. 이후 8단계로 확인한다.

## 11. 정리 [로컬]

```bash
terraform -chdir=infra destroy
```

EC2, 보안 그룹, Data EBS attachment만 삭제된다. Data EBS는 `infra/data-ebs`의 별도 state에 있어 남는다. 다음 배포에서 같은 `data_volume_id`로 다시 연결한다. `infra/data-ebs`는 destroy하지 않는다.

## 12. 문제 해결

| 증상 | 원인과 조치 |
| --- | --- |
| Compose가 `deploy/prod/backend.env not found`로 실행을 거부한다 | 6단계의 env 파일을 만들지 않았다. |
| 로그인은 되는데 이후 요청이 `401`이다 | HTTP에서 `SESSION_COOKIE_SECURE=true`다. 6단계의 테스트 예외를 확인하고 재실행한다. |
| `up`할 때 8080 포트가 이미 사용 중이다 | 이전 프로젝트 이름으로 실행한 스택이 남아 있다. `docker compose -p store-expiration-tracker-local -f compose.ec2.yaml down`으로 내린 뒤 다시 실행한다. ([PR #66](https://github.com/J4EU/Store-Expiration-Tracker/pull/66)) |
| SSH나 `:8080` 접속이 timeout된다 | 현재 공인 IP가 `allowed_operator_cidrs`에 없다. 값을 갱신하고 `terraform -chdir=infra apply`를 다시 실행한다. |
| `findmnt` 출력이 없다 | user data가 아직 실행 중이거나 실패했다. `/var/log/cloud-init-output.log`를 확인한다. |
