# Public Surface and Secret Handling

## 현재 선택

외부 HTTP 진입점은 Nginx다. 현재 외부 health endpoint는 `GET /api/health`이며, Nginx가 `/api` prefix를 제거해 FastAPI의 내부 `GET /health` route로 전달한다. `/health` 자체는 외부 health endpoint가 아니다.

업무 데이터 API는 인증된 운영자 session을 요구한다. 반면 로그인, 로그아웃, 현재 session 확인 endpoint는 인증 흐름을 시작하거나 상태를 확인하기 위해 비인증 요청을 허용한다. 이 경계는 업무 데이터를 공개한다는 뜻이 아니다.

production runtime 설정에서는 FastAPI의 `/docs`, `/openapi.json`, `/redoc`을 비활성화한다. 현재 secret은 아래 두 환경변수다.

- `ADMIN_PASSWORD`
- `SESSION_SECRET`

secret 원문과 session cookie/token은 Git, 문서, 로그에 남기지 않는다. port, API path, CORS allowlist, cookie `Secure` 여부는 secret이 아니라 runtime configuration으로 다룬다. 다만 내부 host나 운영 구조를 드러내는 실제 값은 sensitive configuration으로 보고 공개 문서에 고정하지 않는다.

production secret에는 개인 운영 계정과 실제 실행에 필요한 최소 주체만 접근하게 한다. 파일로 보관한다면 일반적으로 소유자 중심의 최소 권한을 적용하되, 이는 운영체제의 `root`까지 접근할 수 없다는 뜻은 아니다.

정기 rotation은 현재 운영 규칙으로 두지 않는다. 대신 노출이나 계정 공유가 의심되거나, 운영 디바이스를 분실하거나, 운영 환경을 이전하는 사건이 생기면 관련 secret을 변경한다. 자동 rotation은 secret 관리 서비스나 배포 자동화가 필요해질 때 재검토한다.

사고 대응은 영향 범위에 따라 구분한다.

- 일반 secret 변경은 애플리케이션 재시작 또는 재배포로 반영한다.
- secret 노출이 의심되면 필요 시 접근을 차단하고, secret 교체와 재배포 뒤 session 무효화를 확인한다.
- EC2 host 침해가 의심되면 기존 host를 신뢰하지 않고 격리하며, 기존 secret을 폐기한 뒤 깨끗한 배포 단위에서 복구한다. Host 침해를 Compose restart만으로 처리하지 않는다.

## 선택 이유

이 서비스는 공개 API 소비자나 공개 회원가입을 제공하지 않는 단일 운영자 도구다. 따라서 health 확인에 필요한 최소 경로와 인증 bootstrap 경로를 제외한 업무 데이터 API를 공개할 이유가 없다.

API 문서 UI는 local development에서는 구현 확인에 유용하지만, production 외부 공개에 필요한 기능은 아니다. 또한 `ADMIN_PASSWORD`와 `SESSION_SECRET`은 각각 운영자 인증과 session 서명에 직접 영향을 주므로 일반 설정값과 분리해 취급한다.

## 수용한 trade-off

- `/api/health`는 Nginx와 prefix 제거 규칙에 의존한다. proxy 경계가 바뀌면 health check 경로도 함께 검증해야 한다.
- `SESSION_SECRET`을 변경하면 기존 signed session은 모두 무효화된다.
- `ADMIN_PASSWORD` 변경은 다음 애플리케이션 시작 시 운영자 계정 비밀번호에 반영된다.
- 이 결정은 secret 저장·주입 기술을 확정하지 않는다. 실제 production에서 어떤 env 파일이나 주입 방식을 쓰는지는 repository만으로 확인되지 않는다.
- Secure cookie production 정책에는 HTTPS가 필요하지만, 현재 repository의 EC2/Nginx 구성에는 TLS termination과 443 구성이 없다.

## 재검토 조건

- 외부 API 소비자, 공개 시연, 별도 monitoring system이 추가될 때
- health check에 인증 상태, 의존성 상태, 더 상세한 운영 정보를 포함해야 할 때
- secret 회전, 접근 권한, 보관 위치에 대한 반복 가능한 운영 절차가 필요할 때
- HTTPS와 실제 production 공개 구조를 도입하거나 변경할 때

현재 요청 경계와 `/api/health`의 전달 구조는 [Application and Request Flow](../architecture/application-and-request-flow.md)에서 다룬다. session의 선택과 한계는 [Operator Session Policy](operator-session-policy.md)를 따른다.

## References

- [Issue #22](https://github.com/J4EU/Store-Expiration-Tracker/issues/22)
- [PR #35](https://github.com/J4EU/Store-Expiration-Tracker/pull/35)
