# EC2 인증서 백업·복원

이 문서는 EC2를 다시 만들 때 기존 Let's Encrypt 인증서를 로컬로 백업했다가 새 EC2에 복원하는 절차를 기록한다. 인증서를 새로 발급하는 절차는 [EC2 Manual Deploy Runbook](ec2-manual-deploy.md)의 6단계를 따른다.

## 배경

- 인증서는 EC2 루트 볼륨의 `/etc/letsencrypt`에 있다. 루트 볼륨은 EC2와 함께 삭제되므로, EC2를 다시 만들면 인증서도 사라진다([Issue #96](https://github.com/J4EU/Store-Expiration-Tracker/issues/96)).
- 런북은 이때 6단계로 인증서를 다시 발급한다는 전제로 쓰여 있다. 6단계는 staging 시험 발급, Cloudflare TXT 레코드 수동 입력과 전파 확인, 실제 발급, TXT 삭제를 사람이 직접 한다.
- [Issue #115](https://github.com/J4EU/Store-Expiration-Tracker/issues/115)에서 Data EBS를 교체하려고 EC2를 다시 만들면서, 재발급 대신 이 문서의 절차로 기존 인증서를 옮겼다.

## 수명

이 문서는 EC2를 다시 만들면 인증서가 사라지는 문제(#96)가 해결될 때까지만 쓰는 임시 절차다. #96이 해결되면 이 문서도 정리한다. 인증서 갱신 방식은 [Issue #92](https://github.com/J4EU/Store-Expiration-Tracker/issues/92)에서 다룬다.

## 전제

- 기존 EC2가 아직 있고, `/etc/letsencrypt/live/store.j4eu.dev/`에 실제 인증서가 있다.
- 기존 EC2와 새 EC2는 같은 EIP를 쓴다. 그래서 `<public_ip>`는 두 EC2에서 같다.

명령의 실행 위치는 각 단계 제목에 `[로컬]`, `[EC2]`로 표시한다.

## 1. 백업 파일 만들기 [EC2]

`terraform -chdir=infra destroy`를 실행하기 **전에** 기존 EC2에서 진행한다.

```bash
sudo tar -czpf /tmp/letsencrypt.tar.gz -C /etc letsencrypt
sudo chown ec2-user /tmp/letsencrypt.tar.gz
```

- `live/store.j4eu.dev/`의 `*.pem`은 `archive/`의 파일을 가리키는 심볼릭 링크다. 파일을 하나씩 복사하지 않고 `tar`로 묶어 링크 구조를 유지한다.
- `-p`로 권한을 보존하고, `-C /etc letsencrypt`로 `letsencrypt/...` 경로로 묶는다.
- `chown`은 다음 단계에서 `ec2-user`로 내려받기 위해서다.

## 2. 로컬로 가져오기 [로컬]

백업에는 개인 키(`privkey.pem`)가 들어 있다. repo 밖 디렉터리에 두고 권한을 좁힌다.

```bash
mkdir -p ~/backup/letsencrypt && chmod 700 ~/backup/letsencrypt
scp -i <private_key_path> ec2-user@<public_ip>:/tmp/letsencrypt.tar.gz ~/backup/letsencrypt/
chmod 600 ~/backup/letsencrypt/letsencrypt.tar.gz
```

링크가 보존됐는지 확인한다.

```bash
tar -tzvf ~/backup/letsencrypt/letsencrypt.tar.gz | grep "live/store.j4eu.dev"
```

`fullchain.pem -> ../../archive/...`처럼 `->`로 표시되면 링크가 보존된 것이다.

## 3. EC2 다시 만들기 [로컬]

백업을 확인한 뒤에 기존 EC2를 지우고 새로 만든다. 절차는 런북의 12단계(정리)와 2단계(인프라 생성)를 따른다.

## 4. 새 EC2에 복원하기 [로컬 → EC2]

새 EC2는 같은 EIP를 쓰지만 호스트 키가 바뀐다. 그래서 접속하기 전에 known_hosts에서 기존 EC2의 항목을 지운다. 지우지 않으면 호스트 키 불일치 경고로 SSH 접속이 막힌다.

```bash
ssh-keygen -R <public_ip>
```

백업 파일을 올린다. [로컬]

```bash
scp -i <private_key_path> ~/backup/letsencrypt/letsencrypt.tar.gz ec2-user@<public_ip>:/tmp/
```

`/etc` 아래에 풀고 업로드한 파일을 지운다. [EC2]

```bash
sudo tar -xzpf /tmp/letsencrypt.tar.gz -C /etc && rm /tmp/letsencrypt.tar.gz
```

## 5. 확인

인증서 파일이 복원됐는지 확인한다. [EC2]

```bash
sudo openssl x509 -in /etc/letsencrypt/live/store.j4eu.dev/fullchain.pem -noout -issuer -dates
```

발급자가 staging이 아닌 실제 Let's Encrypt이고 만료일이 남아 있으면 복원된 것이다.

파일 확인만으로는 Nginx가 복원한 인증서로 HTTPS를 처리하는지 알 수 없다. 런북 3단계(SSH 접속과 Data EBS mount 확인)부터 9단계(동작 확인)까지 진행하되, 6단계(인증서 준비)는 건너뛴다. [로컬 · EC2]

- 9단계의 `nginx -t`가 성공하면 Nginx가 복원한 인증서와 개인 키를 읽을 수 있다.
- 9단계의 `curl`과 브라우저 확인이 통과하면 복원한 인증서로 HTTPS가 동작하는 것이다.

## 6. 로컬 백업 지우기 [로컬]

5단계에서 HTTPS 동작까지 확인한 뒤 로컬 백업을 지운다.

```bash
rm -rf ~/backup/letsencrypt
```
