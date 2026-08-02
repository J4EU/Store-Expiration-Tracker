# 배포 전 인증 검증 Runbook 초안

## 목적

이 문서는 1차 운영 배포 전후에 인증 관련 동작을 실제 배포 URL 기준으로 확인하기 위한 Runbook 초안이다.

체크리스트의 목적은 새 정책을 정하는 것이 아니라, Issue #21과 Issue #22에서 정한 production 기준이 실제 배포 환경에서 맞게 동작하는지 확인하는 것이다.

## 사용 시점

아래 상황에서 이 문서를 연다.

- 1차 운영 배포 직전
- production 환경변수 또는 reverse proxy 설정을 바꾼 직후
- 인증 / 세션 / 쿠키 관련 코드를 바꾼 뒤 배포할 때
- 배포 후 로그인, 세션 유지, 보호 API 접근이 흔들리는지 확인할 때

## 배포 정보 기록

```text
검증 일시:
검증자:
배포 URL:
프론트 빌드 기준:
백엔드 배포 기준:
배포 방식:
관련 이슈:
관련 커밋:
```

## 1. 배포 전 설정 확인

- [ ] production의 `VITE_API_BASE_URL`이 `/api`인지 확인한다.
  - 기대 결과: 프론트가 배포 URL 기준 `/api/...`로 요청한다.
  - 결과:

- [ ] production의 `SESSION_COOKIE_SECURE`가 `true`인지 확인한다.
  - 기대 결과: HTTPS 배포 환경에서 인증 쿠키가 `Secure` 조건으로 발급된다.
  - 결과:

- [ ] production의 `API_DOCS_ENABLED`가 `false`인지 확인한다.
  - 기대 결과: FastAPI 문서 UI와 OpenAPI 명세가 production에서 공개되지 않는다.
  - 결과:

- [ ] production secret이 Git, 문서, 로그에 원문으로 남지 않는지 확인한다.
  - 기대 결과: `ADMIN_PASSWORD`, `SESSION_SECRET` 실제 값이 repo와 로그에 노출되지 않는다.
  - 결과:

- [ ] production 환경변수 주입 방식이 수동 `export`에 의존하지 않는지 확인한다.
  - 기대 결과: 재시작 또는 재배포 후에도 같은 설정을 재현할 수 있다.
  - 결과:

- [ ] FastAPI가 외부에 직접 노출되지 않는 배치인지 확인한다.
  - 기대 결과: 외부 사용자는 Nginx 공개 URL을 통해서만 API에 접근한다.
  - 결과:

## 2. 공개 경로 확인

아래 명령의 `https://example.com`은 실제 배포 URL로 바꿔서 실행한다.

- [ ] `GET /health`가 공개되어 있는지 확인한다.

```bash
curl -i https://example.com/health
```

기대 결과:

- HTTP 200
- 응답에 내부 설정, DB 경로, secret, 상세 인프라 정보가 없다.

결과:

- [ ] production에서 `/docs`가 공개되지 않는지 확인한다.

```bash
curl -i https://example.com/docs
```

기대 결과:

- 외부에서 API 문서 UI를 볼 수 없다.

결과:

- [ ] production에서 `/openapi.json`이 공개되지 않는지 확인한다.

```bash
curl -i https://example.com/openapi.json
```

기대 결과:

- 외부에서 OpenAPI 명세를 볼 수 없다.

결과:

- [ ] production에서 `/redoc`이 공개되지 않는지 확인한다.

```bash
curl -i https://example.com/redoc
```

기대 결과:

- 외부에서 ReDoc 문서 UI를 볼 수 없다.

결과:

## 3. Reverse proxy 확인

- [ ] `/api` prefix가 FastAPI 기존 라우트로 전달되는지 확인한다.

```bash
curl -i https://example.com/api/health
```

기대 결과:

- Nginx가 `/api` prefix를 제거하는 구성이라면 FastAPI의 `GET /health`로 전달되어 HTTP 200을 반환한다.
- `/api/health`가 실패한다면 Nginx prefix 제거 방식과 Runbook 기대 결과를 함께 재확인한다.

결과:

- [ ] 보호 API가 비로그인 상태에서 차단되는지 확인한다.

```bash
curl -i https://example.com/api/products
```

기대 결과:

- HTTP 401
- 인증 없이 운영 데이터를 읽을 수 없다.

결과:

## 4. 브라우저 로그인 확인

- [ ] 배포 URL에 접속했을 때 로그인 화면이 표시되는지 확인한다.
  - 기대 결과: 비로그인 사용자는 운영 화면을 바로 볼 수 없다.
  - 결과:

- [ ] 올바른 운영자 비밀번호로 로그인한다.
  - 기대 결과: 로그인 성공 후 운영 화면으로 진입한다.
  - 결과:

- [ ] 로그인 후 새로고침해도 세션이 유지되는지 확인한다.
  - 기대 결과: 새로고침 후에도 운영 화면이 유지된다.
  - 결과:

- [ ] 로그아웃 후 운영 화면 접근이 차단되는지 확인한다.
  - 기대 결과: 세션이 해제되고 로그인 화면으로 돌아간다.
  - 결과:

## 5. 쿠키 확인

브라우저 개발자 도구에서 세션 쿠키를 확인한다.

- [ ] 세션 쿠키 이름이 의도한 이름인지 확인한다.
  - 기대 결과: `store_expiration_session`
  - 결과:

- [ ] 쿠키에 `HttpOnly`가 적용되어 있는지 확인한다.
  - 기대 결과: JavaScript에서 세션 쿠키를 직접 읽을 수 없다.
  - 결과:

- [ ] HTTPS production에서 쿠키에 `Secure`가 적용되어 있는지 확인한다.
  - 기대 결과: HTTPS 연결에서만 쿠키가 전송된다.
  - 결과:

- [ ] 쿠키 `SameSite`가 `Lax` 기준인지 확인한다.
  - 기대 결과: same origin 운영 구조에 맞는 기본 방어선을 유지한다.
  - 결과:

- [ ] 쿠키 위변조 시 세션이 거부되는지 확인한다.
  - 기대 결과: 쿠키 값을 임의로 바꾸면 로그인 상태가 유지되지 않는다.
  - 결과:

## 6. 세션 만료 확인

- [ ] 세션 만료 시간이 정책과 맞는지 확인한다.
  - 기대 결과: 고정 4시간 만료 기준을 따른다.
  - 결과:

- [ ] 세션 만료 후 보호 화면 접근 시 로그인 화면으로 돌아가는지 확인한다.
  - 기대 결과: 만료된 세션으로 운영 API를 계속 사용할 수 없다.
  - 결과:

## 7. CORS 확인

- [ ] production에서 개발용 origin을 그대로 넓게 열어두지 않았는지 확인한다.
  - 기대 결과: same origin 기준을 기본값으로 두며, 개발용 `localhost`, `127.0.0.1`, `5173`, `4173` allowlist를 production 기준으로 그대로 사용하지 않는다.
  - 결과:

- [ ] 브라우저 네트워크 탭에서 API 요청 origin과 cookie 전송을 확인한다.
  - 기대 결과: 배포 URL 기준 same origin 요청으로 동작하고, 로그인 후 API 요청에 세션 쿠키가 포함된다.
  - 결과:

## 8. 실패 시 처리

검증 실패 항목은 이 Runbook에서 즉석으로 정책을 바꾸지 않는다.
아래 형식으로 후속 작업에 남긴다.

```text
실패 항목:
관찰 결과:
기대 결과:
관련 설정 또는 코드 후보:
배포 계속 여부:
후속 이슈:
```

배포 계속 여부는 아래 기준으로 나눈다.

- `중단`: 인증 우회, 보호 API 공개, secret 노출, production 공개 범위 위반
- `보류`: 로그인은 되지만 세션 유지, 쿠키 속성, CORS, reverse proxy 기대 결과가 흔들리는 경우
- `진행 가능`: 문서 표현, 기록 누락, 재검증 필요처럼 운영 접근 제어를 직접 깨지 않는 경우

## 9. 배포 후 기록

```text
최종 결과:
남은 위험:
후속 이슈:
다음 배포 때 먼저 확인할 항목:
```
