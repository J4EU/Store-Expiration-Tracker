# EC2 Manual Deploy Runbook

이 문서는 새 EC2에서 Store Expiration Tracker를 실행하기까지의 현재 수동 배포 절차를 순서대로 기록한다. Terraform 레이어 구조와 Data EBS 자동화의 설명은 [EC2 배포 인프라](../../infra/README.md)를 따르고, 이 문서는 실행 순서와 명령만 다룬다.

## 전제와 범위

현재 절차는 아래 상태를 전제로 한다.

- 외부 진입점은 `https://store.j4eu.dev`다. `http://`로 온 요청은 HTTPS로 301 리다이렉트된다([Issue #74](https://github.com/J4EU/Store-Expiration-Tracker/issues/74)).
- 도메인 `store.j4eu.dev`의 A 레코드는 EIP를 가리키고, DNS는 Cloudflare에서 관리한다.
- TLS 인증서는 Let's Encrypt에서 수동 DNS-01로 발급해 EC2 루트 볼륨의 `/etc/letsencrypt`에 둔다. 루트 볼륨은 EC2와 함께 삭제되므로, EC2를 새로 만들면 6단계로 인증서를 다시 발급한다.
- backend 환경변수는 EC2 checkout 안의 `deploy/prod/backend.env` 파일로 주입한다.
- 이미지는 EC2에서 직접 build한다. 이미지 registry는 쓰지 않는다.
- EC2를 start해도 컨테이너는 자동으로 시작되지 않는다.

이 문서가 다루지 않는 것:

- 인증서 보관 위치와 갱신 방식 ([Issue #92](https://github.com/J4EU/Store-Expiration-Tracker/issues/92))
- 시크릿 주입 방식 고도화 ([Issue #65](https://github.com/J4EU/Store-Expiration-Tracker/issues/65))
- 이미지 registry, 배포 자동화, 백업·복원

명령의 실행 위치는 각 단계 제목에 `[로컬]`, `[EC2]`, `[Cloudflare]`로 표시한다.

## 1. 사전 준비 [로컬]

- AWS 자격증명이 설정되어 있고 Terraform(`>= 1.15.0`)이 설치되어 있다.
- `ap-northeast-2`에 EC2 키 페어가 있고, 그 private key 파일을 로컬에 가지고 있다. 기본 키 페어 이름은 `j4eu-ec2`다.
- EC2에 접속할 네트워크에서 그 네트워크의 공인 IPv4를 확인할 수 있다.
- Cloudflare에서 `j4eu.dev`의 DNS 레코드를 편집할 수 있다.

## 2. 인프라 생성 [로컬]

저장소 최상위에서 시작한다.

### 2-1. Data EBS 준비

기존 Data EBS를 다시 쓰는 경우 새로 만들지 않는다. `data_volume_id` output이 있는지만 확인한다.

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

### 2-2. EIP 준비

기존 EIP를 다시 쓰는 경우 새로 만들지 않는다. `allocation_id` output이 있는지만 확인한다.

```bash
terraform -chdir=infra/eip output allocation_id
```

EIP가 아직 없을 때만 새로 만든다. 필수 변수가 없어 `terraform.tfvars`는 만들지 않는다.

```bash
terraform -chdir=infra/eip init
terraform -chdir=infra/eip apply
terraform -chdir=infra/eip output public_ip
```

이 주소가 서비스의 고정 공인 IP다. 한 번 destroy한 EIP 주소는 다시 받을 수 없으므로 `infra/eip`는 destroy하지 않는다.

### 2-3. EC2 생성

`infra/terraform.tfvars`가 없으면 예시 파일을 복사한다.

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

`infra/terraform.tfvars`에 아래 값을 입력한다.

- `allowed_operator_cidrs`: EC2에 접속할 네트워크의 공인 IPv4를 `/32`로 입력한다. 그 네트워크에서 아래 명령으로 확인한다.

  ```bash
  curl -s https://checkip.amazonaws.com
  ```

Data EBS 볼륨 ID와 EIP allocation ID는 입력하지 않는다. EC2 레이어가 `infra/data-ebs/terraform.tfstate`의 `data_volume_id`와 `infra/eip/terraform.tfstate`의 `allocation_id` output을 읽는다. 그래서 2-1과 2-2를 먼저 끝내야 한다.

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

## 6. 인증서 준비

Nginx는 `/etc/letsencrypt/live/store.j4eu.dev/`의 인증서가 있어야 시작한다. 인증서는 certbot 컨테이너로 수동 DNS-01 발급한다. 실제 발급 전에 staging 인증서로 절차를 먼저 시험한다.

### 6-1. 도메인 연결 확인 [로컬]

도메인의 A 레코드가 EIP를 가리키는지 확인한다.

```bash
terraform -chdir=infra/eip output -raw public_ip
dig +short store.j4eu.dev A @1.1.1.1
dig +short store.j4eu.dev A @8.8.8.8
```

세 값이 같으면 연결이 맞다. `dig` 결과가 Cloudflare 주소면 레코드가 proxy 상태이므로 DNS only로 바꾼다.

### 6-2. 발급 전 상태 확인 [EC2]

```bash
sudo ls -la /etc/letsencrypt
sudo docker run --rm certbot/certbot --version
```

처음 발급이면 `/etc/letsencrypt`에서 `No such file or directory`가 나오는 것이 정상이다.

### 6-3. staging 인증서로 시험 [EC2]

```bash
sudo docker run -it --rm --name certbot \
  -v "/etc/letsencrypt:/etc/letsencrypt" \
  -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
  certbot/certbot certonly \
  --manual --preferred-challenges dns \
  --staging \
  -d store.j4eu.dev
```

이메일과 약관 질문에 답하면 TXT 값이 나온다. 이때 Enter를 누르지 않고 아래 두 단계를 먼저 한다.

1. [Cloudflare] `j4eu.dev` → DNS → Records에 TXT 레코드를 추가한다.
   - Type: `TXT`
   - Name: `_acme-challenge.store`
   - Content: 터미널에 나온 값
   - TTL: Auto
2. [로컬] 전파를 확인한다.

   ```bash
   dig +short TXT _acme-challenge.store.j4eu.dev @1.1.1.1
   dig +short TXT _acme-challenge.store.j4eu.dev @8.8.8.8
   dig +short TXT _acme-challenge.store.j4eu.dev @wally.ns.cloudflare.com
   ```

세 곳 모두 터미널의 값과 같으면 EC2에서 Enter를 누른다.

staging 인증서를 확인한다.

```bash
sudo ls -la /etc/letsencrypt/live/store.j4eu.dev/
sudo openssl x509 -in /etc/letsencrypt/live/store.j4eu.dev/fullchain.pem -noout -subject -issuer -dates
sudo ls -ld /etc/letsencrypt/live /etc/letsencrypt/archive
```

`live/`의 파일은 `../../archive/...`를 가리키는 링크이고, issuer에 `(STAGING)`이 붙어 있어야 한다.

### 6-4. 실제 인증서 발급 [EC2]

6-3의 명령에서 `--staging`만 뺀다.

```bash
sudo docker run -it --rm --name certbot \
  -v "/etc/letsencrypt:/etc/letsencrypt" \
  -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
  certbot/certbot certonly \
  --manual --preferred-challenges dns \
  -d store.j4eu.dev
```

- 이메일과 약관을 다시 묻는다. 기존 인증서가 있다는 질문에는 교체(Renew & replace)를 고른다.
- 새 TXT 값이 나오면 6-3의 Cloudflare 입력과 전파 확인을 반복한다. 기존 TXT 레코드는 Content만 새 값으로 바꾼다.
- 실제 서버는 검증 실패가 1시간에 5회까지다. 전파를 확인한 뒤에 Enter를 누른다.

실제 인증서를 확인한다.

```bash
sudo openssl x509 -in /etc/letsencrypt/live/store.j4eu.dev/fullchain.pem -noout -issuer -dates
```

issuer에 `(STAGING)`이 없고 만료일이 보여야 한다.

### 6-5. TXT 레코드 정리 [Cloudflare]

검증이 끝나 더는 필요 없으므로 `_acme-challenge.store` TXT 레코드를 지운다.

## 7. env 파일 준비 [EC2]

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

`SESSION_COOKIE_SECURE=true`는 그대로 둔다. HTTPS에서만 session cookie를 보내도록 하는 값이다.

secret 원문은 Git, 문서, 이슈, PR, 채팅에 남기지 않는다.

`deploy/prod/backend.env`는 AI 에이전트가 읽을 수 있는 범위에서 벗어나도록 로컬에 두지 않고 EC2에서만 작성한다([Issue #65](https://github.com/J4EU/Store-Expiration-Tracker/issues/65)).

## 8. 실행 [EC2]

```bash
docker compose -f compose.ec2.yaml up --build --wait
```

이미지를 EC2에서 직접 build하므로 첫 실행은 시간이 걸린다. `--wait`는 detached mode로 실행하고, health check가 있는 backend는 `healthy`, health check가 없는 nginx는 `running` 상태가 될 때까지 기다린다.

## 9. 동작 확인

### [EC2]

```bash
docker compose -f compose.ec2.yaml ps
docker compose -f compose.ec2.yaml exec nginx nginx -t
```

- 두 서비스가 `running`이고 backend가 `healthy`다.
- `nginx -t`가 성공한다. Nginx가 인증서와 개인 키를 읽을 수 있다는 뜻이다.

### [로컬]

```bash
curl -s https://store.j4eu.dev/api/health
curl -sI "http://store.j4eu.dev/items?x=1"
```

- health 응답이 `{"status":"ok"}`다.
- HTTP 요청이 `301`이고, `Location`이 경로와 쿼리를 유지한 `https://store.j4eu.dev/items?x=1`이다.

### [로컬 브라우저]

1. `https://store.j4eu.dev`에 경고 없이 접속되는지 확인한다.
2. `admin`과 `ADMIN_PASSWORD`로 로그인한다.
3. 상품 하나를 등록하고 목록에 나타나는지 확인한다.
4. 새로고침해도 로그인이 유지되는지 확인한다.
5. DevTools의 쿠키 목록에서 `store_expiration_session`에 Secure와 HttpOnly가 표시되는지 확인한다.

### [EC2]

SQLite 파일이 Data EBS에 만들어졌는지 확인한다.

```bash
sudo ls -l /srv/store-expiration-tracker/data
```

`store_expiration_tracker.db`가 있으면 배포가 끝난 것이다.

## 10. EC2 stop/start 후 재기동

EC2를 start해도 컨테이너는 자동으로 시작되지 않는다. public IP는 EIP이므로 stop/start 뒤에도 바뀌지 않는다. 인증서도 루트 볼륨에 남아 있어 다시 발급하지 않는다.

[EC2] SSH로 접속해 mount를 확인한 뒤 실행한다.

```bash
findmnt /srv/store-expiration-tracker/data
cd Store-Expiration-Tracker
docker compose -f compose.ec2.yaml up --wait
```

이후 9단계로 확인한다. 기존 데이터가 그대로 보여야 한다.

## 11. 코드 변경 재배포 [EC2]

```bash
cd Store-Expiration-Tracker
git pull
docker compose -f compose.ec2.yaml up --build --wait
```

`deploy/prod/backend.env`는 Git이 추적하지 않으므로 `git pull`로 바뀌지 않는다. `backend.env.example`에 새 변수가 추가됐다면 직접 반영한다.

`backend.env`를 바꾼 뒤에는 backend 컨테이너를 다시 만들어야 반영된다. `restart`는 env_file을 다시 읽지 않는다.

```bash
docker compose -f compose.ec2.yaml up -d --force-recreate backend
```

이후 9단계로 확인한다.

## 12. 정리 [로컬]

```bash
terraform -chdir=infra destroy
```

EC2, 보안 그룹, Data EBS attachment, EIP association만 삭제된다. Data EBS와 EIP는 각각 `infra/data-ebs`, `infra/eip`의 별도 state에 있어 남는다. 다음 배포에서 EC2 레이어가 두 state의 output을 읽어 다시 연결하므로, 새 EC2도 같은 public IP를 쓴다. `infra/data-ebs`와 `infra/eip`는 destroy하지 않는다. EC2 레이어의 destroy도 두 state 파일을 읽으므로, 이 파일들을 지우거나 옮기기 전에 EC2 레이어를 먼저 정리한다.

EC2의 루트 볼륨도 함께 삭제되므로 `/etc/letsencrypt`의 인증서도 사라진다. 다음 배포에서는 6단계로 인증서를 다시 발급한다.

EIP는 EC2가 없는 동안에도 공인 IPv4 요금이 부과된다.

## 13. 문제 해결

| 증상 | 원인과 조치 |
| --- | --- |
| Compose가 `deploy/prod/backend.env not found`로 실행을 거부한다 | 7단계의 env 파일을 만들지 않았다. |
| `up`할 때 nginx가 시작하지 못한다 | `/etc/letsencrypt/live/store.j4eu.dev/`에 인증서가 없다. 6단계로 인증서를 발급한다. `docker compose -f compose.ec2.yaml logs nginx`로 원인을 확인한다. |
| `backend.env`를 바꿨는데 반영되지 않는다 | `restart`는 env_file을 다시 읽지 않는다. 11단계처럼 `--force-recreate`로 backend를 다시 만든다. |
| IP로 HTTPS 접속하면 인증서 오류가 난다 | 인증서는 `store.j4eu.dev`용이다. IP가 아니라 도메인으로 접속한다. |
| 2-3의 `plan`/`apply`가 `Unable to find remote state`로 실패한다 | `infra/data-ebs/terraform.tfstate` 또는 `infra/eip/terraform.tfstate`가 없다. 에러가 가리키는 경로에 따라 2-1 또는 2-2를 먼저 apply한다. |
| 2-3의 `plan`/`apply`가 `This object does not have an attribute named "data_volume_id"`로 실패한다 | `infra/data-ebs` state는 있지만 Data EBS가 없다. 2-1에서 Data EBS를 먼저 apply한다. |
| 2-3의 `plan`/`apply`가 `This object does not have an attribute named "allocation_id"`로 실패한다 | `infra/eip` state는 있지만 EIP가 없다. 2-2에서 EIP를 먼저 apply한다. |
| `up`할 때 80 포트가 이미 사용 중이다 | 이전 프로젝트 이름으로 실행한 스택이 남아 있다. `docker compose -p store-expiration-tracker-local -f compose.ec2.yaml down`으로 내린 뒤 다시 실행한다. ([PR #66](https://github.com/J4EU/Store-Expiration-Tracker/pull/66)) |
| SSH나 HTTP(`80`)·HTTPS(`443`) 접속이 timeout된다 | 현재 공인 IP가 `allowed_operator_cidrs`에 없다. 값을 갱신하고 `terraform -chdir=infra apply`를 다시 실행한다. |
| `findmnt` 출력이 없다 | user data가 아직 실행 중이거나 실패했다. `/var/log/cloud-init-output.log`를 확인한다. |
