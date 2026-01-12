# Flask Template 기능별 상세 테스트 가이드

이 문서는 Flask Production Template에 구현된 주요 확장 기능들을 직접 테스트하고 검증하는 방법을 단계별로 설명합니다.

## 사전 준비 (Prerequisites)

테스트를 진행하기 전에 로컬 개발 환경이 실행 중이어야 합니다.

```bash
# 1. 가상환경 활성화 (Python 기반 테스트 시)
source venv/bin/activate

# 2. Docker 서비스 실행 (DB, Redis, Worker, Flower, Nginx)
docker-compose up -d

# 3. Flask 개발 서버 실행 (터미널 1)
flask run

# 4. Celery 워커 실행 (터미널 2 - Docker 미사용 시 필요)
# docker-compose를 사용 중이라면 생략 가능
celery -A celery_worker.celery worker --loglevel=info
```

---

## 1. OAuth2 소셜 로그인 (Google)

구글 로그인은 브라우저 리다이렉션이 필요하므로 웹 브라우저를 통해 테스트합니다.

### 테스트 방법
1. 브라우저에서 `http://localhost:5000/api/v1/auth/google/login` 접속
2. 구글 로그인 페이지로 리다이렉트 되는지 확인
3. (실제 로그인은 구글 Cloud Console 설정 및 콜백 처리가 완료되어야 가능)

> **참고**: `.env` 파일에 `GOOGLE_CLIENT_ID`와 `GOOGLE_CLIENT_SECRET`이 설정되어 있어야 합니다.

---

## 2. WebSocket 실시간 통신 (Flask-SocketIO)

제공된 HTML 클라이언트 예제를 사용하여 WebSocket 연결 및 메시지 송수신을 테스트합니다.

### 테스트 방법
1. `examples/websocket_client.html` 파일을 브라우저로 엽니다.
   - Chrome 기준: `File` -> `Open File...` -> `examples/websocket_client.html` 선택
2. **"Status: Connected"** 메시지가 나타나는지 확인합니다.
3. **"Send Test Message"** 버튼을 클릭합니다.
4. 서버 로그(터미널)와 브라우저 화면에 메시지 전송/수신 로그가 찍히는지 확인합니다.

---

## 3. Redis 캐싱 (Caching)

`UserService.get_users` 메서드에 적용된 `@cached` 데코레이터를 검증합니다.

### 테스트 방법 (cURL)

**첫 번째 요청 (Cache Miss):**
```bash
# 시간 측정과 함께 요청
time curl -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" http://localhost:5000/api/v1/users
```
- 예상 결과: DB 조회로 인해 상대적으로 느림, Prometheus 메트릭의 `cache_misses` 증가

**두 번째 요청 (Cache Hit):**
```bash
time curl -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" http://localhost:5000/api/v1/users
```
- 예상 결과: **즉각적인 응답 (매우 빠름)**, Prometheus 메트릭의 `cache_hits` 증가

---

## 4. Prometheus 메트릭 (Metrics)

애플리케이션 및 시스템 메트릭이 정상적으로 수집되는지 확인합니다.

### 테스트 방법
1. 브라우저 또는 cURL로 `http://localhost:5000/metrics` 접속
2. 다음과 같은 메트릭 키워드가 포함되어 있는지 검색 (`Cmd+F`):
   - `flask_http_request_duration_seconds`
   - `app_user_registrations_total`
   - `app_cache_hits_total`
   - `process_cpu_seconds_total`

---

## 5. Sentry 에러 트래킹 (Error Tracking)

Sentry 연동 확인을 위해 테스트용 에러를 유발하거나 설정을 확인합니다.

### 테스트 방법
1. `.env` 파일에 유효한 `SENTRY_DSN`이 설정되어 있는지 확인합니다.
2. 실행 시 로그에 `[Sentry] Initializing SDK...` 관련 메시지가 있는지 확인합니다.
3. (선택) 임의의 에러를 발생시키는 임시 라우트를 만들어 접속해봅니다.
   ```python
   # app/api/v1/health.py 등에 임시 추가
   @api.route('/error')
   class ErrorTest(Resource):
       def get(self):
           1 / 0  # ZeroDivisionError 발생 -> Sentry 전송
   ```

---

## 6. API 버저닝 (v1 vs v2) 및 마이그레이션

v1(기존) API와 v2(개선된) API의 응답 구조 차이를 확인합니다.

### 테스트 방법 (cURL)

**v1 API 호출 (Deprecated):**
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:5000/api/v1/users
```
- 응답 구조: `users` 리스트가 최상위에 위치
- 헤더 확인: `API-Version: 1.0` (기본값)

**v2 API 호출 (Recommended):**
```bash
curl -H "Authorization: Bearer <TOKEN>" \
     -H "API-Version: 2.0" \
     http://localhost:5000/api/v2/users
```
- 응답 구조: `data`, `pagination`, `metadata`, `links` 구조
- `metadata`에 `response_time_ms` 등이 포함되어 있는지 확인

---

## 7. 고급 페이지네이션 (Pagination)

v2 API에서 HATEOAS 링크와 Link Header를 확인합니다.

### 테스트 방법
```bash
curl -v -H "Authorization: Bearer <TOKEN>" \
     "http://localhost:5000/api/v2/users?page=1&per_page=5"
```

**확인 사항:**
1. **Response Body**: `links` 객체에 `self`, `next`, `last` 등의 URL이 포함됨
2. **Response Header**: `Link` 헤더에 `<http://...>; rel="next"` 형태의 문자열 존재
3. **Custom Headers**: `X-Total-Count`, `X-Total-Pages` 헤더 존재

---

## 8. Celery Flower 대시보드

비동기 작업 모니터링 대시보드 접근을 확인합니다.

### 테스트 방법
1. 브라우저에서 `http://localhost/flower/` 접속 (마지막 슬래시 중요)
2. 로그인 창이 뜨면 아래 정보 입력:
   - **User**: `admin`
   - **Password**: `change_me` (또는 .env 설정값)
3. 대시보드 진입 후 `Workers` 탭에서 `celery@flask_celery_worker` 상태가 **Online**인지 확인

---

## 9. CI/CD 파이프라인 (GitHub Actions)

자동화된 테스트 및 빌드 파이프라인 동작을 확인합니다.

### 테스트 방법
1. 코드를 GitHub 레포지토리에 푸시합니다.
2. GitHub 레포지토리의 **Actions** 탭으로 이동합니다.
3. **CI (Tests & Lint)** 워크플로우가 초록색 체크(✅)로 통과하는지 확인합니다.
4. 태그 푸시 시 (`git tag v1.0.0 && git push --tags`) **CD (Docker Build)** 워크플로우가 실행되는지 확인합니다.

---

## 10. 전체 자동 테스트 실행

작성된 **pytest** 테스트 코드를 통해 기능 전반을 검증합니다.

```bash
# 전체 테스트 실행
pytest -v

# 특정 기능 테스트
pytest tests/test_auth.py      # 인증, OAuth 등
pytest tests/test_pagination.py # 페이지네이션 v1/v2
pytest tests/test_cache.py      # 캐싱 로직
```
