# Issue #28 SPA fallback and routing policy

## 목적

이 문서는 Issue #28에서 확인한 SPA fallback 현상과 현재 MVP의 화면 URL 정책을 정리한다.

핵심은 아래 세 가지를 분리하는 것이다.

- 프론트 화면 진입 URL
- 백엔드 API 요청 URL
- 브라우저 주소창에 남는 경로

## 확인한 현상

Vite 개발 서버와 preview 서버는 정의되지 않은 프론트 경로도 SPA fallback으로 처리할 수 있다.

예를 들어 아래 경로로 직접 들어가도 Vue 앱이 열린다.

```text
http://localhost:5173/auth/session
http://localhost:5173/dashboard
```

이 경로들은 현재 MVP의 공식 화면 URL이 아니다.
하지만 fallback으로 `index.html`이 반환되면 `App.vue`가 실행되고, 인증 상태에 따라 로그인 화면이나 운영 화면이 표시된다.

그 결과 로그인 성공 후 화면은 대시보드인데 주소창은 `/auth/session`처럼 API처럼 보이는 경로로 남을 수 있다.

## API 경로 정책

프론트는 API를 `/api/...` 경로로 호출한다.

```text
VITE_API_BASE_URL=/api
```

로컬 개발에서는 Vite dev server가 `/api` prefix를 제거해 FastAPI 기존 라우트로 전달한다.

```text
브라우저 요청: http://localhost:5173/api/auth/session
Vite proxy:   /api/auth/session -> http://localhost:8000/auth/session
FastAPI:      /auth/session
```

production에서는 Nginx가 같은 책임을 맡는다.
따라서 FastAPI 라우트를 `/api/...`로 바꾸지 않는다.

`/api`는 API 존재를 숨기기 위한 장치가 아니다.
프론트 정적 파일 요청과 백엔드 API 요청을 나누는 namespace다.
보호 목표는 FastAPI 서버와 내부 포트를 외부에 직접 노출하지 않는 것이다.

## Vue Router를 도입하지 않는 이유

현재 MVP는 Vue Router를 사용하지 않는다.
화면 전환은 `App.vue` 내부의 `currentView` 상태가 담당한다.

```text
currentView = "dashboard"
currentView = "archive"
```

Issue #28의 목표는 URL 혼선을 줄이는 것이지, 화면별 URL 라우팅을 새로 설계하는 것이 아니다.

Vue Router를 도입하면 아래 결정이 함께 필요해진다.

- `/login`, `/dashboard`, `/archive`를 공식 URL로 둘지
- 로그인하지 않은 사용자가 `/dashboard`로 들어왔을 때 어디로 보낼지
- 로그인된 사용자가 `/login`으로 들어왔을 때 어디로 보낼지
- 세션 확인 중에는 어떤 route 상태로 둘지
- `/archive` 직접 진입 시 archive 데이터를 언제 로드할지
- 브라우저 뒤로가기와 `dashboard/archive` 전환을 어떻게 연결할지
- 정의되지 않은 route를 404로 둘지, redirect할지

이 결정들은 현재 MVP의 화면 구조보다 크다.
따라서 Issue #28에서는 Vue Router를 도입하지 않는다.

## 현재 fallback URL 정책

현재 MVP의 공식 프론트 화면 URL은 `/` 하나로 둔다.

`/auth/session`, `/dashboard`, `/test`처럼 fallback으로 Vue 앱이 열린 경로는 공식 화면 URL로 보지 않는다.

앱 부팅 시 브라우저 주소창 경로가 `/`가 아니면 `history.replaceState`로 `/`로 정규화한다.

```text
http://localhost:5173/auth/session -> http://localhost:5173/
http://localhost:5173/dashboard    -> http://localhost:5173/
```

이 정규화는 redirect 응답이 아니라 브라우저에서 실행되는 클라이언트 측 주소 정리다.
잘못된 fallback URL이 사용자의 history에 남지 않도록 `replaceState`를 사용한다.

## 로그인 후 URL 정책

로그인 성공 후 `/dashboard`로 이동시키지 않는다.

이유는 현재 MVP에서 `/dashboard`를 공식 화면 URL로 제공하지 않기 때문이다.

로그인 성공 후에는 기존처럼 내부 상태를 갱신하고 대시보드 데이터를 불러온다.

```text
로그인 성공
-> authenticated = true
-> currentView = "dashboard"
-> dashboard data load
-> 주소창은 /
```

따라서 화면과 URL의 관계는 아래처럼 둔다.

```text
/          -> 앱 진입점
dashboard  -> URL이 아니라 currentView 상태
archive    -> URL이 아니라 currentView 상태
/api/...   -> 백엔드 API 요청 namespace
```

## 보안 판단

확인된 SPA fallback 현상 자체는 인증 우회나 데이터 노출이 아니다.

예를 들어 `/auth/session`으로 직접 들어갔을 때 Vue 앱이 열리는 것은 프론트 fallback 동작이다.
반면 `/api/auth/session`으로 들어갔을 때 JSON이 보이는 것은 API 요청이 Vite proxy를 거쳐 FastAPI로 전달된 정상 응답이다.

문제가 되는 것은 아래 경우다.

- FastAPI 서버나 내부 포트가 production에서 외부에 직접 노출되는 경우
- 보호 API가 인증 없이 데이터를 반환하는 경우
- session cookie, secret, production `.env` 값이 노출되는 경우
- production reverse proxy가 `/api` prefix를 의도와 다르게 전달하는 경우

이 항목들은 production 배포 구조와 함께 Issue #27 및 배포 전 검증 흐름에서 확인한다.

preview 환경에서 확인한 `/api` 호출은 production Nginx reverse proxy 검증을 대체하지 않는다.
실제 `/api` prefix 제거와 FastAPI 직접 노출 차단은 배포 구조가 확정된 뒤 별도로 확인한다.

## 한계와 후속 결정 조건

이 결정은 현재 MVP의 최소 라우팅 정책이다.

아래 요구가 생기면 Vue Router 또는 명시적 라우팅 정책을 별도 이슈에서 다시 검토한다.

- `/dashboard`, `/archive`를 북마크하거나 공유해야 한다.
- 브라우저 뒤로가기로 화면 전환 상태를 복원해야 한다.
- 로그인 전후 route guard가 필요하다.
- 정의되지 않은 URL에 404 화면을 보여줘야 한다.
- 화면별 deep link가 운영 흐름에 필요하다.

그 전까지는 `/` 하나를 공식 화면 URL로 두고, API 요청은 `/api/...`로 분리한다.
