# EC2 Compose 검증 스파이크

이 Terraform 구성은 EC2 한 대에서 현재 Docker Compose 경로를 직접 확인하는
데 필요한 AWS 리소스만 만든다.

생성하는 리소스는 아래와 같다.

- default VPC 안의 Amazon Linux 2023 `t3.micro` EC2 인스턴스 1대
  - 루트 디스크로 20GB `gp3` EBS 사용
- `allowed_operator_cidr`에서만 SSH와 현재 Compose Nginx 포트(`8080`)를
  허용하는 보안 그룹 1개

이번 단계에서는 설계 완성도보다 수동 운영 관찰을 우선한다. Terraform은
EC2와 Security Group 생성에만 책임을 둔다. EC2와 수명 주기를 분리한 별도
데이터 EBS와 Elastic IP는 만들지 않는다.

EC2 내부의 초기화, Docker 설치, 애플리케이션 배포는 `user_data`나 자동화에
넣지 않고 SSH로 직접 수행한다. HTTPS와 CI/CD도 이번 스파이크 범위에
포함하지 않는다.

## apply 전에 할 일

로컬 변수 파일을 만들고, 예시로 적힌 주소를 현재 사용 중인 공인 IPv4 주소로
바꾼다.

```bash
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars`는 Git에서 제외된다. 사용할 기존 EC2 키 페어는 기본값으로
`j4eu-ec2`를 사용한다.

## 수동 Terraform 실행 흐름

```bash
terraform init
terraform plan
terraform apply
```

- apply가 끝나면 `public_ip` 출력값으로 EC2에 SSH 접속한다.
- Docker와 Docker Compose를 직접 설치하고, 저장소 밖에 secret 파일을 준비한 뒤, 현재 Compose 스택을 실행한다.
- 임시 확인 URL은 `http://<public_ip>:8080`이다.

## 스파이크 검증 결과

이 구성으로 EC2와 Security Group을 생성하고, SSH로 접속해 Git, Docker,
Docker Compose, Docker Buildx 등 필요한 호스트 환경을 수동으로 준비했다.
이후 현재 Compose 스택을 빌드·실행하고, `SESSION_COOKIE_SECURE` 설정을
임시 조정해 브라우저에서 로그인 및 인증 동작까지 확인했다.

이 과정에서 HTTP URL(`http://<public_ip>:8080`)과
`SESSION_COOKIE_SECURE=true`를 함께 사용했을 때 로그인 후 인증이 필요한
요청이 `401`로 실패하는 것을 확인했다.

HTTP 경로 확인에 한해서만 EC2의 Git 밖 secret 파일에서
`SESSION_COOKIE_SECURE=false`로 임시 변경한 뒤 로그인 및 인증이 정상적으로
동작하는 것을 확인했다.

Secure cookie 정책이 원인일 가능성은 있지만, 이번 스파이크에서는 브라우저
cookie storage나 쿠키 헤더의 실제 동작까지 직접 확인하지 않았다.

`false`는 HTTPS가 적용된 실제 운영 환경의 설정이 아니다.

확인 후 `terraform destroy`로 생성한 EC2와 Security Group을 정리했다.

## 이번 스파이크에서 확인하지 않은 것

- HTTPS URL에서 `SESSION_COOKIE_SECURE=true`를 유지한 로그인 세션
- EC2와 수명 주기를 분리한 EBS, SQLite 데이터 보존 및 복구
- 재부팅·EC2 교체 이후의 Compose 자동 시작과 데이터 재연결
- 백업·복구, Elastic IP, CI/CD
