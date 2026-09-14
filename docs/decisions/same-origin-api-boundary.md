# Same-Origin API Boundary

## 현재 선택

repository의 deployment configuration은 frontend와 backend를 하나의 외부 origin 아래에 둔다. 브라우저는 API를 `/api/...`로 요청하고, Nginx가 `/api` prefix를 제거해 FastAPI의 기존 route로 전달한다.

FastAPI route 자체를 `/api/...`로 바꾸지 않는다. local development에서는 Vite development proxy가 같은 prefix 제거 책임을 맡는다.

## 선택 이유

- frontend 정적 파일과 API를 Nginx 단일 외부 진입점에서 구분할 수 있다.
- browser 요청은 같은 origin 안에서 처리하므로 development용 CORS allowlist나 cross-site cookie 문제를 production 기본 경계로 가져오지 않는다.
- backend는 host port를 직접 열지 않고 Compose 내부 연결로 제한할 수 있다.
- 기존 FastAPI route를 유지해 backend route와 browser-facing namespace의 책임을 분리할 수 있다.

## 수용한 trade-off

- `/api`는 API를 숨기는 보안 장치가 아니라 경계 표기다. 보호는 backend 인증과 backend host port를 직접 공개하지 않는 구성에 의존한다.
- reverse proxy 설정이 browser-facing API 경로의 일부가 되므로, prefix 전달이 바뀌면 frontend와 proxy를 함께 검증해야 한다.
- 이 선택은 실제 production URL과 HTTPS가 이미 검증됐다는 뜻이 아니다. 현재 repository에는 TLS termination과 443 구성도 없다.

SPA fallback의 현재 동작, `/api/health` 경로, local Vite 대응 구조는 [Application and Request Flow](../architecture/application-and-request-flow.md)에서 다룬다.

## 재검토 조건

- frontend와 API를 별도 origin 또는 별도 배포 단위로 운영해야 할 때
- 외부 API 소비자나 다른 서비스의 API 연동이 필요할 때
- API gateway, 별도 authentication boundary, CDN/정적 호스팅 분리가 실제 요구가 될 때

## References

- [Issue #21](https://github.com/J4EU/Store-Expiration-Tracker/issues/21)
- [Issue #28](https://github.com/J4EU/Store-Expiration-Tracker/issues/28)
- [PR #30](https://github.com/J4EU/Store-Expiration-Tracker/pull/30)
- [PR #42](https://github.com/J4EU/Store-Expiration-Tracker/pull/42)
