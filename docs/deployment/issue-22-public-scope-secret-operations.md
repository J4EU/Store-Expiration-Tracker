# Issue #22 Review: 운영 배포 공개 범위와 비밀값 운영 기준 정리

## 문서 목적

이 문서는 GitHub Issue `#22 운영 배포 공개 범위와 비밀값 운영 기준 정리`를 현재 repo 기준으로 다시 정리한 결과를 담는다.

이번 이슈의 핵심은 인증 기능을 더 크게 확장하는 것이 아니다.
운영 배포 전에 어떤 경로를 공개로 둘지, 어떤 값을 비밀값으로 취급할지, 그리고 비밀값 변경이 인증 상태에 어떤 영향을 주는지 설명 가능하게 만드는 것이 목적이다.

특히 아래 질문에 대한 현재 결론과 후속 배포 설계로 넘길 범위를 고정한다.

- production에서 `/docs`, `/openapi.json`, `/redoc`을 공개할 것인가
- `GET /health` 외에 인증 없이 열어둘 엔드포인트가 필요한가
- 현재 repo에서 secret으로 취급할 값은 무엇인가
- secret과 일반 환경 설정값을 어떻게 구분할 것인가
- secret을 Git, 문서, 로그에 남기지 않는 기준은 무엇인가
- secret 변경 시 서버 재시작, 운영자 계정, 기존 세션에 어떤 영향이 있는가
- secret 저장/주입 방식은 이번 이슈에서 어디까지 결정할 것인가

## 현재 구현 상태

현재 repo에는 접근 제어 1차 구현이 들어가 있다.

- `GET /health`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/session`
- `GET /health` 제외 운영 API 보호
- `ADMIN_PASSWORD`, `SESSION_SECRET` 환경변수 사용
- signed session cookie 기반 인증

현재 FastAPI 앱은 기본 설정으로 생성되어 있으므로, 별도 설정을 하지 않으면 `/docs`와 `/openapi.json`도 열린다.
따라서 운영 배포 전에 이 경로를 production에서 그대로 공개할지 결정해야 한다.

## 이슈가 열린 이유

Issue #20에서는 signed session cookie 방식과 배포 쿠키 기준을 정리했다.
Issue #21에서는 로컬/배포 연결 설정과 환경변수 주입 원칙을 정리했다.

하지만 실제 운영 배포에서는 설정 항목을 나누는 것만으로는 충분하지 않다.
어떤 경로를 공개로 남길지, 어떤 값이 secret인지, secret을 누가 보고 바꿀 수 있는지, 변경이 세션에 어떤 영향을 주는지도 함께 설명할 수 있어야 한다.

이번 이슈는 `환경변수를 어떤 기술로 주입할 것인가`를 확정하는 이슈가 아니다.
어떤 주입 방식을 쓰더라도 지켜야 하는 공개 범위와 secret 운영 기준을 정리하는 이슈다.

## 이번 검토에서 다시 고정한 기준

### 1. Production에서는 `/docs`, `/openapi.json`, `/redoc`을 닫는다

`/docs`는 사람이 브라우저에서 보는 API 문서 UI다.
`/openapi.json`은 API 문서 UI와 도구가 읽는 OpenAPI 명세 JSON이다.
`/redoc`도 같은 OpenAPI 명세를 렌더링하는 문서 UI다.

이 문서 경로들은 DB 데이터를 직접 노출하지는 않는다.
하지만 운영 배포에서 열려 있으면 현재 서버가 가진 API 경로, 요청 schema, 응답 schema가 외부에 드러난다.

현재 서비스는 아래 성격을 가진다.

- 개인 운영 도구
- 단일 운영자
- 공개 API 소비자 없음
- 외부 회원가입 없음

따라서 production에서 API 문서를 공개할 필요가 크지 않다.
개발 편의는 local/development에서만 유지하고, production에서는 `/docs`, `/openapi.json`, `/redoc`을 닫는 기준으로 둔다.

```text
development:
/docs 공개
/openapi.json 공개
/redoc 공개

production:
/docs 비공개
/openapi.json 비공개
/redoc 비공개
```

### 2. 공개 엔드포인트는 `GET /health`만 둔다

현재 production에서 인증 없이 열어둘 필요가 있는 엔드포인트는 `GET /health`뿐이다.

`GET /health`는 배포 상태 확인과 모니터링을 위한 최소 공개 경로로 둔다.
다만 health 응답에는 내부 설정, DB 경로, secret, 상세 인프라 정보를 넣지 않는다.
현재처럼 `status` 수준의 최소 응답만 공개한다.

추후 포트폴리오 공개나 외부 사용자 시연을 위해 일부 경로를 열어야 할 요구가 생기면, 그때 별도 이슈에서 공개 범위를 다시 검토한다.

### 3. 현재 production secret은 `ADMIN_PASSWORD`, `SESSION_SECRET`이다

현재 repo에서 secret으로 취급할 값은 아래 두 가지다.

```text
ADMIN_PASSWORD
SESSION_SECRET
```

`ADMIN_PASSWORD`는 운영자 로그인 권한을 부여하는 값이다.
노출되면 공격자가 `/auth/login`으로 로그인해 운영 API를 사용할 수 있다.

`SESSION_SECRET`은 세션 쿠키 서명에 사용하는 값이다.
현재 세션 쿠키는 서버가 payload에 서명한 값이고, 요청 시 서버는 같은 secret으로 서명을 검증한다.
따라서 `SESSION_SECRET`이 노출되면 유효한 로그인 세션을 위조할 위험이 생긴다.

이 둘은 모두 Git, 문서, 로그에 남기지 않는 secret으로 다룬다.

### 4. 포트 번호와 API URL은 secret이 아니라 config다

포트 번호, API base URL, CORS allowlist, 쿠키 `secure` 여부는 환경별로 달라지는 설정값이다.
하지만 이 값들은 일반적으로 secret으로 분류하지 않는다.

예시는 아래와 같다.

```text
PORT=8000
VITE_API_BASE_URL=/api
CORS_ALLOW_ORIGINS=...
SESSION_COOKIE_SECURE=true 또는 false
API_DOCS_ENABLED=true 또는 false
```

이 값들이 노출된다고 해서 곧바로 인증 우회나 세션 위조가 가능한 것은 아니다.
따라서 `ADMIN_PASSWORD`, `SESSION_SECRET`과 같은 secret과 구분한다.

다만 production 내부 URL, 사설 DB host, 관리자 전용 내부 주소처럼 인프라 구조를 드러내는 값은 sensitive config로 볼 수 있다.
sensitive config는 secret은 아니지만 공개 문서에 실제 값을 박제하지 않는다.

### 5. Secret은 Git, 문서, 로그에 남기지 않는다

production secret은 아래 위치에 원문으로 남기지 않는다.

- Git commit
- README와 docs 문서
- issue와 PR 본문
- application log
- access log
- debug log
- 터미널 출력 캡처

금지 대상은 secret 원문만이 아니다.
아래 값도 로그에 남기지 않는다.

- `ADMIN_PASSWORD`
- `SESSION_SECRET`
- session cookie/token
- production `.env` 전체 내용
- secret이 포함된 환경변수 전체 출력

특히 디버깅 목적으로 환경변수 전체를 출력하지 않는다.
필요하면 변수 존재 여부나 설정 모드만 확인하고, 실제 값은 마스킹한다.

### 6. Production secret 접근 권한은 최소화한다

production secret은 개인 운영 계정과 애플리케이션 실행에 필요한 최소 프로세스만 접근할 수 있게 둔다.

서버 파일로 secret을 둘 경우, 원칙은 아래와 같다.

```text
소유자: 애플리케이션을 배포/실행하는 서버 계정
권한: 소유자만 읽고 쓸 수 있음
```

예시는 아래와 같다.

```bash
chown app-user:app-user .env
chmod 600 .env
```

`chmod 600`은 파일 소유자만 읽고 쓸 수 있게 한다.
다만 운영체제의 `root` 권한을 가진 주체는 파일을 읽을 수 있으므로, 완전한 의미의 `나만 접근`은 아니다.
따라서 문서 기준은 `개인 운영 계정과 애플리케이션 실행 프로세스에 필요한 최소 권한`으로 둔다.

### 7. Secret 변경 반영에는 애플리케이션 재시작 또는 재배포가 필요하다

현재 구현에서 `ADMIN_PASSWORD`, `SESSION_SECRET`은 서버 프로세스가 환경변수에서 읽는다.
또한 설정을 읽는 `get_settings()`는 캐시되어 실행 중 변경을 동적으로 반영하지 않는다.

따라서 `.env`나 환경변수 주입 값을 바꿔도 이미 실행 중인 서버 프로세스에는 자동 반영되지 않는다.
변경을 적용하려면 애플리케이션 프로세스 재시작 또는 재배포가 필요하다.

### 8. `ADMIN_PASSWORD` 변경은 서버 시작 시 운영자 비밀번호 갱신으로 반영된다

현재 구현은 서버 시작 시 관리자 계정을 확인한다.
환경변수의 `ADMIN_PASSWORD`와 DB에 저장된 admin 비밀번호 해시가 다르면, DB의 admin 비밀번호를 새 값 기준으로 갱신한다.

따라서 `ADMIN_PASSWORD` 변경 절차는 아래처럼 이해한다.

```text
1. production secret 값을 새 ADMIN_PASSWORD로 교체한다.
2. 애플리케이션을 재시작 또는 재배포한다.
3. 서버 시작 시 admin 계정 비밀번호가 새 값 기준으로 갱신된다.
```

### 9. `SESSION_SECRET` 변경은 기존 세션 전체 무효화로 취급한다

현재 세션 쿠키는 `SESSION_SECRET`으로 서명된다.
요청이 들어오면 서버는 같은 secret으로 서명을 다시 계산해 쿠키가 서버가 만든 값인지 검증한다.

따라서 `SESSION_SECRET`이 바뀌면 기존 쿠키의 서명은 새 secret 기준으로 더 이상 유효하지 않다.
결과적으로 기존 로그인 세션은 모두 무효화된다.

이 동작은 사고 대응 시 전체 로그아웃 수단으로 사용할 수 있다.
다만 평상시 변경도 운영자 재로그인을 발생시키므로, 변경 시점은 의도적으로 잡아야 한다.

### 10. Secret 변경과 회전은 필요 시 수행한다

현재 단계에서는 정기 secret rotation을 운영 규칙으로 두지 않는다.
secret 수가 적고, 운영자가 1명이며, 자동 회전 체계를 운영할 만큼 배포 구조가 아직 크지 않기 때문이다.

따라서 1차 기준은 아래와 같다.

- 평상시에는 필요할 때만 secret을 변경한다.
- 노출 의심, 계정 공유 의심, 디바이스 분실, 운영 환경 이전 같은 상황에서 변경한다.
- 정기 회전은 secret 관리 서비스나 배포 자동화가 필요해지는 시점에 다시 검토한다.

### 11. 사고 대응은 범위별로 나눈다

보안 사고 대응 기준은 `항상 EC2 종료`로 두지 않는다.
사고 범위에 따라 대응 수준을 나눈다.

secret 값만 노출된 것으로 의심되는 경우에는 아래 절차를 우선한다.

```text
1. 필요하면 외부 접근을 일시 차단한다.
2. 노출 의심 secret을 교체한다.
3. 애플리케이션을 재시작 또는 재배포한다.
4. 로그인과 기존 세션 무효화 여부를 확인한다.
```

Docker Compose 배포라면 일반적인 secret 변경은 compose 서비스 재시작 또는 컨테이너 재배포로 반영할 수 있다.

반면 EC2 호스트 자체가 침해되었을 가능성이 있으면 compose 재시작만으로 충분하지 않다.
이 경우에는 EC2를 네트워크에서 격리하고, 기존 secret을 폐기한 뒤 깨끗한 배포 단위에서 새 secret을 주입해 복구한다.

즉 운영 절차는 아래처럼 나눈다.

```text
일반 secret 변경:
애플리케이션 재시작 또는 컨테이너 재배포

secret 노출 의심:
secret 교체, 애플리케이션 재시작 또는 컨테이너 재배포, 세션 무효화 확인

EC2 침해 의심:
EC2 네트워크 격리, 기존 secret 폐기, 깨끗한 배포 단위에서 복구
```

## Secret 저장/주입 방식의 결정 범위

production secret 저장/주입 방식은 이번 이슈에서 확정하지 않는다.
구체 방식은 실제 배포 설계 이슈에서 Docker Compose, 서버 `.env`, systemd `EnvironmentFile`, CI/CD secret 주입 여부와 함께 결정한다.

이번 이슈에서는 아래 원칙만 고정한다.

- production secret은 Git 밖에서 관리한다.
- 수동 `export`는 production 표준 실행 방식으로 사용하지 않는다.
- production secret은 반복 가능한 방식으로 주입한다.
- 어떤 주입 방식을 쓰더라도 secret 원문은 Git, 문서, 로그에 남기지 않는다.
- secret이 담긴 파일 또는 설정은 최소 접근 권한으로 제한한다.

현재 1차 후보는 서버 `.env` 또는 Docker Compose `env_file`이다.
하지만 Docker Compose의 실제 환경변수 주입 방식은 배포 구조와 함께 학습 및 결정한다.

## Issue #21과의 범위 구분

Issue #21은 로컬과 production에서 달라지는 설정 주입 구조를 정리한다.
Issue #22는 그 설정 중 secret의 운영 책임과 공개 범위 기준을 정리한다.

따라서 두 이슈의 경계는 아래와 같다.

```text
Issue #21:
환경별 설정 항목을 나누고, 수동 export를 표준 실행 방식에서 제외한다.

Issue #22:
production 공개 범위와 secret 운영 기준을 정한다.
구체적인 secret 저장/주입 기술은 후속 배포 설계로 넘긴다.
```

이 기준은 Issue #21과 충돌하지 않는다.
#21에서 Docker Compose `env_file` 또는 `environment`를 1차 후보로 둔 것은 주입 구조 후보를 정리한 것이고, #22에서는 그 후보를 확정하지 않는다.
#22는 어떤 후보를 선택하더라도 지켜야 할 secret 관리 기준만 고정한다.

## 결론

### 1. Production 공개 엔드포인트는 `GET /health`만 둔다

production에서 인증 없이 열어둘 경로는 `GET /health`로 한정한다.
`/docs`, `/openapi.json`, `/redoc`은 local/development 편의로만 열고 production에서는 닫는다.
그 외 운영 API와 인증 API는 로그인 뒤에 둔다.

### 2. Secret은 `ADMIN_PASSWORD`, `SESSION_SECRET`이다

현재 repo에서 production secret으로 취급할 값은 `ADMIN_PASSWORD`, `SESSION_SECRET`이다.
포트 번호, API URL, CORS allowlist, 쿠키 `secure` 여부는 secret이 아니라 환경별 config로 본다.

### 3. Secret은 저장 위치보다 운영 기준을 먼저 고정한다

production secret은 Git, 문서, 로그에 남기지 않는다.
session cookie/token과 production `.env` 전체 출력도 금지한다.
secret 저장/주입 방식은 이번 이슈에서 확정하지 않고, 실제 배포 설계 이슈에서 배포 구조와 함께 결정한다.

### 4. Secret 변경은 필요 시 수행한다

정기 secret rotation은 아직 운영 규칙으로 두지 않는다.
노출 의심, 디바이스 분실, 운영 환경 이전, 사고 대응처럼 필요한 상황에서 변경한다.
변경 반영에는 애플리케이션 재시작 또는 재배포가 필요하다.

## 이번 결정으로 정리되는 규칙

- production에서 `/docs`, `/openapi.json`, `/redoc`은 닫는다.
- production 공개 엔드포인트는 `GET /health`만 둔다.
- `GET /health` 응답에는 내부 설정, DB 경로, secret, 상세 인프라 정보를 넣지 않는다.
- 현재 production secret은 `ADMIN_PASSWORD`, `SESSION_SECRET`이다.
- 포트 번호, API URL, CORS allowlist, 쿠키 `secure` 여부는 secret이 아니라 config다.
- production 내부 URL이나 사설 host처럼 운영 구조를 드러내는 값은 sensitive config로 보고 실제 값을 공개 문서에 박제하지 않는다.
- secret은 Git, 문서, 로그에 원문으로 남기지 않는다.
- session cookie/token과 production `.env` 전체 출력도 로그 금지 대상으로 둔다.
- production secret 접근 권한은 개인 운영 계정과 애플리케이션 실행에 필요한 최소 프로세스로 제한한다.
- 서버 파일로 secret을 둘 경우 소유자만 읽고 쓸 수 있는 권한을 기준으로 둔다.
- `ADMIN_PASSWORD`, `SESSION_SECRET` 변경 반영에는 애플리케이션 재시작 또는 재배포가 필요하다.
- `ADMIN_PASSWORD` 변경은 서버 시작 시 admin 계정 비밀번호 갱신으로 반영된다.
- `SESSION_SECRET` 변경은 기존 세션 전체 무효화로 취급한다.
- 정기 secret rotation은 1차 운영 기준으로 두지 않는다.
- secret 변경은 필요 시 수행한다.
- 사고 대응은 일반 secret 변경, secret 노출 의심, EC2 침해 의심으로 나눈다.
- secret 저장/주입 방식은 이번 이슈에서 확정하지 않고 후속 배포 설계 이슈에서 결정한다.
- 현재 1차 후보는 서버 `.env` 또는 Docker Compose `env_file`이다.
- Issue #21과 #22는 각각 환경변수 주입 구조와 secret 운영 기준으로 역할을 나눈다.

## 다음 반영 후보

- production 공개 범위 검증을 Issue #23 배포 전 인증 검증 체크리스트와 Runbook으로 실행하기
- 실제 배포 설계 이슈에서 secret 저장/주입 방식을 결정하기
- Docker Compose `env_file`과 서버 `.env`의 차이를 학습한 뒤 1차 배포 구조에 반영하기
