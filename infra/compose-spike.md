# EC2 Compose 검증 스파이크

이 문서는 Data EBS 분리 이전에 EC2 한 대에서 현재 Docker Compose 구성이 실제로
빌드·실행되는지 확인한 스파이크 기록이다. 현재 배포 인프라의 구성과 운영 기준은
[EC2 배포 인프라](README.md)를 따른다.

## 당시 구성 범위

스파이크 당시 Terraform은 아래 리소스만 만들었다.

- default VPC 안의 Amazon Linux 2023 `t3.micro` EC2 인스턴스 1대
  - Root EBS로 20GB `gp3` 사용
- `allowed_operator_cidr`에서만 SSH와 Compose Nginx 포트(`8080`)를 허용하는
  보안 그룹 1개

EC2 내부 초기화, Docker 설치, 애플리케이션 배포는 `user_data`나 자동화에 넣지
않고 SSH로 직접 수행했다. 별도 Data EBS, Elastic IP, HTTPS, CI/CD는 이 스파이크에
포함하지 않았다.

## 관찰 결과

EC2와 Security Group을 생성한 뒤 SSH로 접속해 Git, Docker, Docker Compose,
Docker Buildx를 수동으로 준비했다. 이어서 Compose 스택을 빌드·실행하고,
브라우저 로그인과 인증 동작을 확인했다.

HTTP URL(`http://<public_ip>:8080`)에서 `SESSION_COOKIE_SECURE=true`를 사용하면
로그인 뒤 인증이 필요한 요청이 `401`로 실패했다. HTTP 경로 확인에 한해서만
EC2의 Git 밖 secret 파일에서 `SESSION_COOKIE_SECURE=false`로 임시 변경한 뒤
로그인과 인증 동작을 확인했다.

Secure cookie 정책이 원인일 가능성은 있지만, 이 스파이크에서는 브라우저의 cookie
storage나 `Set-Cookie`/`Cookie` 헤더를 직접 확인하지 않았다. 따라서 이 결과는
HTTPS 운영 환경의 세션 동작을 검증한 것이 아니다.

확인 뒤 `terraform destroy`로 당시 생성한 EC2와 Security Group을 정리했다.

## 확인하지 않은 것

- HTTPS URL에서 `SESSION_COOKIE_SECURE=true`를 유지한 로그인 세션
- EC2 교체 뒤 SQLite 데이터 보존과 재연결
- 재부팅·EC2 교체 이후의 Compose 자동 시작
- 백업·복구, Elastic IP, CI/CD
