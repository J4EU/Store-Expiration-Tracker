# Operator Session Policy

## 현재 선택

현재 서비스는 단일 점포의 단일 운영자 도구를 전제로, 서버 저장 세션이 아닌 서명된 session cookie로 운영자 인증을 처리한다.

- 공개 회원가입은 제공하지 않는다.
- 운영자 계정은 서버 시작 시 환경변수의 관리자 비밀번호를 기준으로 준비한다.
- session payload는 사용자명과 만료 시각만 담고 서버 서명으로 검증한다.
- session은 로그인 시점부터 최대 4시간 동안 유효하다.
- cookie는 `HttpOnly`, `SameSite=Lax`, path `/`로 발급한다.
- cookie `domain`은 지정하지 않고 host-only로 둔다.
- `Secure` 속성은 `SESSION_COOKIE_SECURE` runtime 설정을 따른다.

## 선택 이유

현재 인증의 목적은 복잡한 사용자 관리가 아니라 운영 화면과 업무 데이터 API를 보호하는 것이다. 단일 운영자와 단순한 session 정보 범위에서는 별도 세션 저장소, 만료 정리, 기기별 세션 관리를 바로 도입하는 비용보다 서명된 cookie가 더 작은 구성이다.

4시간은 임의의 숫자가 아니라, 실제 로그인이 대체로 19시 이후에 이뤄지는 흐름에서 사용 중 불편을 크게 늘리지 않으면서 퇴근 후 점포 PC에 session이 오래 남는 위험을 줄이기 위한 상한이다.

JWT도 stateless signed token으로 사용하면 개별 token을 즉시 무효화하기 어렵다는 한계가 유사하다. 현재 단일 서비스에서는 추가 복잡도에 비해 얻는 이점이 작아 별도로 도입하지 않는다.

## 수용한 trade-off

- 서버가 개별 session을 저장하지 않으므로 특정 session만 즉시 강제 무효화하는 기능은 없다.
- 탈취된 signed cookie는 서버가 원래 브라우저에서 온 요청인지 구별할 수 없어 만료 전까지 replay될 수 있다.
- `SESSION_SECRET`을 변경하면 기존 signed session은 모두 무효화된다.
- 무활동 시간 기준 자동 로그아웃은 현재 구현하지 않는다.
- production에서 Secure cookie 정책을 사용하려면 HTTPS가 필요하다. 현재 repository의 EC2/Nginx 구성에는 TLS termination이 없으므로, HTTPS는 이 정책을 실제 production에서 충족하기 위한 미완료 prerequisite다.

## 재검토 조건

아래 요구가 생기면 server-side session 또는 더 큰 인증 모델을 다시 검토한다.

- 여러 운영자 또는 역할별 권한이 필요할 때
- 특정 기기나 session을 즉시 종료해야 할 때
- 비밀번호 변경 뒤 session 관리 정책이 더 세분화돼야 할 때
- 외부 사용자, 공개 가입, 여러 서비스 간 인증 연동이 필요할 때
- 서브도메인 사이에서 같은 인증 cookie를 공유해야 할 때

## References

- [Issue #20](https://github.com/J4EU/Store-Expiration-Tracker/issues/20)
- [PR #35](https://github.com/J4EU/Store-Expiration-Tracker/pull/35)
