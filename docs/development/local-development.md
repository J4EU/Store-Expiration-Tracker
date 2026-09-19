# Local Development

이 문서는 로컬에서 Store-Expiration-Tracker 개발환경을 실행하고 최소 동작을 확인하는 방법을 안내한다.

## 필요한 것

- Python 3
- Node.js와 npm

실제 비밀값은 Git에 넣지 않는다. 백엔드 `.env`와 프론트엔드 `frontend/.env`는 각각 `.gitignore` 대상이다.

## 1. Backend 실행

저장소 루트에서 가상환경과 로컬 설정을 준비한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp deploy/dev/backend.env.example .env
```

`.env`에서 최소한 아래 두 placeholder를 로컬 전용 값으로 바꾼다.

- `ADMIN_PASSWORD`
- `SESSION_SECRET`

그 뒤 환경변수를 현재 셸에 불러오고 서버를 실행한다.

```bash
set -a
source .env
set +a
uvicorn app.main:app --reload
```

서버 시작 과정에서 SQLite DB는 `data/store_expiration_tracker.db`에 자동으로 준비된다. `data/`는 Git에 포함하지 않는다.

로컬 Backend 주소와 개발용 OpenAPI 문서는 아래와 같다.

- API: `http://localhost:8000`
- OpenAPI UI: `http://localhost:8000/docs`
- 상태 확인: `http://localhost:8000/health`

## 2. Frontend 실행

다른 터미널에서 저장소 루트 기준으로 실행한다.

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

브라우저에서 `http://localhost:5173`을 연다.

기본 프론트 설정은 `VITE_API_BASE_URL=/api`다. 개발 서버가 `/api` 요청의 prefix를 제거해 `http://localhost:8000` Backend로 전달하므로, 로컬 개발에서는 별도 API URL을 입력하지 않는다.

## 최소 동작 확인

1. `http://localhost:8000/health`가 정상 응답하는지 확인한다.
2. `http://localhost:5173`에 접속한다.
3. `.env`에 넣은 운영자 비밀번호로 로그인한다. 사용자명은 현재 `admin`이다.
4. `등록 시작 -> 바코드 조회 -> 상품 또는 소비기한 반영` 흐름을 실행한다.
5. 대시보드에서 `오늘 처리`와 `미확인` 목록이 갱신되는지 확인한다.

API의 정확한 endpoint와 요청·응답 형태는 실행 중인 `http://localhost:8000/docs` 또는 `app/main.py`, `app/schemas.py`를 기준으로 확인한다.

## 종료와 자주 확인할 것

- 각 개발 서버는 실행 중인 터미널에서 `Ctrl+C`로 종료한다.
- Backend를 새 셸에서 다시 실행하면 `.env`를 다시 불러와야 한다.
- `SESSION_COOKIE_SECURE=false`는 로컬 HTTP 개발용 설정이다. production 설정이나 실제 production 검증을 뜻하지 않는다.
- Frontend 요청이 실패하면 Backend가 `8000` 포트에서 실행 중인지, `frontend/.env`의 `VITE_API_BASE_URL`이 `/api`인지, Vite 개발 서버를 다시 시작해야 하는 변경이 있었는지 확인한다.
