# Application and Request Flow

이 문서는 현재 repository에 구현된 애플리케이션 요청 경계와 구성 요소의 책임을 설명한다. 정확한 route, Nginx directive, Compose 값은 코드와 설정 파일을 기준으로 확인한다.

## 배포 형태의 요청 흐름

현재 Compose 구성에서 브라우저의 외부 진입점은 Nginx다. 현재 host 공개 포트는 `8080`이며, 이 포트 번호 자체는 장기 정책이 아니라 현재 설정값이다.

```text
Browser
  -> Nginx
       -> frontend 정적 파일과 SPA fallback
       -> /api/... 요청을 backend:8000으로 전달
            -> FastAPI
                 -> SQLite (/app/data)
```

Nginx는 frontend production build를 제공한다. 정적 파일에 해당하지 않는 frontend 경로는 `index.html`로 fallback되며, 현재 MVP의 공식 화면 URL은 `/` 하나다. 화면 전환은 Vue Router가 아니라 Vue 애플리케이션 내부 상태로 처리한다.

`/api/...`는 브라우저 요청과 FastAPI의 내부 route를 구분하는 namespace다. Nginx는 이 prefix를 제거해 FastAPI의 기존 route로 전달한다. `/api` 자체는 `/api/`로 정규화한다. backend 서비스는 Compose에서 host port를 열지 않고 내부 `backend:8000`으로만 연결된다.

## 인증과 health 경계

FastAPI에는 내부 `GET /health` route가 있고, 현재 Compose/Nginx 경로에서 외부 요청은 `/api/health`를 통해 이 route에 도달한다. 반대로 `/health`는 Nginx의 별도 proxy location이 없으므로 현재 설정에서는 SPA fallback 대상이다. 따라서 `/health`를 현재 외부 health endpoint로 보지 않는다.

업무 데이터 API는 인증된 운영자 세션을 요구한다. 로그인, 로그아웃, 현재 세션 확인처럼 인증 흐름을 시작하거나 상태를 확인하는 endpoint는 그와 다른 책임을 가지며, 비로그인 세션 확인은 인증 여부를 응답으로 돌려준다. 공개 업무 데이터 API가 있다는 뜻은 아니다.

## Local development 대응 구조

로컬 개발에서는 Nginx 대신 Vite development proxy가 같은 `/api/...` 경계를 담당한다.

```text
Browser -> Vite development server -> /api/... -> FastAPI
```

Vite도 `/api` prefix를 제거한 뒤 FastAPI의 기존 route로 전달한다. 따라서 local development의 `5173 -> 8000` 연결은 production-like Compose 경로의 Nginx 책임을 개발 환경에서 대응한 것이다.

## SQLite 저장 경계

애플리케이션은 `/app/data` 아래 SQLite 파일을 사용한다. 기본 Compose에서는 `sqlite_data` named volume이 이 경로를 제공해 컨테이너 생명주기와 로컬 DB 파일을 분리한다. EC2용 Compose override에서는 같은 container 경로를 Data EBS가 mount된 host 경로에 bind mount한다.

이 차이는 local named volume이 EC2 교체에도 데이터를 보존한다는 뜻이 아니다. EC2와 Data EBS의 lifecycle 경계는 [Infrastructure and Data Lifecycle](infrastructure-and-data-lifecycle.md)에서 다룬다.

## 현재 확인 범위

이 문서는 repository의 Compose, Nginx, FastAPI, frontend 설정으로 확인되는 구조만 설명한다. 실제 production URL, HTTPS, TLS termination, 실제 운영 환경변수 주입 여부는 이 repository만으로 확인되지 않는다.

## Source of truth

- `compose.yaml`, `compose.ec2.yaml`
- `frontend/nginx.conf`, `frontend/vite.config.js`, `frontend/src/api.js`
- `app/main.py`, `app/auth.py`, `app/db.py`
