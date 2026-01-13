# Flask Template 기능별 상세 테스트 가이드 (Docker & Swagger UI)

이 문서는 **Docker 환경**에서 서비스를 실행하고, **Swagger UI**와 **웹 브라우저**를 사용하여 구현된 기능들을 편리하게 테스트하는 방법을 안내합니다.

## 1. 사전 준비 (Docker 실행)

모든 서비스(App, MySQL, Redis, Worker, Flower, Nginx)를 Docker Compose로 실행합니다.

```bash
# 터미널에서 실행
docker-compose up --build -d
```

---

## 2. 어떤 테스트를 해야 하나요? (Testing Pyramid)

이 프로젝트는 3단계 테스트 전략을 사용합니다. 지금 읽고 계신문서는 **3번 수동 테스트**에 집중합니다.

1.  **단위 테스트 (Unit Test)**: `pytest`로 코드 실행 (가장 빠름) → *[테스트 코드 가이드](test_code_guide.md) 참고*
2.  **통합 테스트 (Integration Test)**: DB, Redis까지 연결해서 테스트
3.  **수동 테스트 (E2E Test)**: 브라우저나 Swagger로 사용자가 직접 확인

---

## 3. 기능별 수동 테스트 (Manual Testing)

### ✅ 테스트 체크리스트
- [ ] Swagger가 열리는가?
- [ ] 회원가입/로그인이 되는가?
- [ ] JWT 토큰으로 인증이 되는가?
- [ ] DB에 데이터가 들어갔는가?

---

### 3.1. API 버저닝 및 인증 (Swagger UI)
(이하 생략...)

### 2.1. API 버저닝 및 인증 (Swagger UI)

Swagger UI를 통해 회원가입, 로그인, 그리고 v1/v2 API 차이를 확인합니다.

1. **Swagger 접속**: [http://localhost/api/v1/docs](http://localhost/api/v1/docs) 접속
2. **회원가입 (Register)**:
   - `Auth` 섹션의 `POST /auth/register` 선택 -> **Try it out**
   - `payload`: `email`, `password` 등 입력 -> **Execute**
   - **Response 201 Created** 확인
3. **로그인 (Login)**:
   - `Auth` 섹션의 `POST /auth/login` 선택 -> **Try it out**
   - 가입한 정보 입력 -> **Execute**
   - **Response Body**에서 `access_token` 복사
4. **인증 토큰 설정**:
   - 우측 상단 **Authorize** 버튼 클릭
   - `Bearer <복사한_액세스_토큰>` 입력 -> **Authorize** -> **Close**
5. **v1 vs v2 비교**:
   - **v1**: `Users` -> `GET /users` 호출 -> 단순 리스트 반환 확인
   - **v2**: [http://localhost/api/v2/docs](http://localhost/api/v2/docs) 접속 및 토큰 설정
   - `Users` -> `GET /users` 호출 -> **Response Body**에 `metadata`, `links`가 포함된 HATEOAS 구조 확인

### 2.2. 고급 페이지네이션 (Swagger UI)

v2 API Swagger에서 링크 헤더와 페이지네이션 동작을 확인합니다.

1. **Swagger v2 접속**: [http://localhost/api/v2/docs](http://localhost/api/v2/docs)
2. `Users` -> `GET /users` 선택
3. **Parameters** 입력:
   - `page`: `1`
   - `per_page`: `5`
4. **Execute** 실행
5. **Server response** 섹션 확인:
   - **Body**: `links` 객체 (`self`, `next` 등) 확인
   - **Headers**: `link` 헤더 (RFC 5988), `x-total-count` 등 커스텀 헤더 확인

### 2.3. Redis 캐싱 (Swagger UI & Logs)

캐싱 적용 여부를 응답 속도와 서버 로그로 확인합니다.

1. **Swagger v1**에서 `GET /users` 준비
2. **첫 번째 Execute**:
   - `docker-compose logs -f app` 명령어로 로그 확인 시 DB 쿼리 로그 발생
   - 응답 시간 확인 (예: 100ms)
3. **두 번째 Execute**:
   - 로그에 DB 쿼리가 발생하지 않음 (캐시 히트)
   - 응답 시간 단축 확인 (예: 5ms)

### 2.4. OAuth2 소셜 로그인 (Browser)

Swagger가 아닌 브라우저 주소창을 이용합니다.

1. 브라우저 주소창 입력: `http://localhost/api/v1/auth/google/login`
2. 구글 로그인 페이지로 리다이렉트 되는지 확인
   - (실제 로그인은 Google Cloud 설정에 등록된 리다이렉트 URI가 일치해야 완료됨)

### 2.5. WebSocket 실시간 통신 (Browser Client)

제공된 테스트용 HTML 파일을 사용합니다.

1. `examples/websocket_client.html` 파일을 브라우저로 열기
2. **Status**가 **Connected**로 변하는지 확인
3. **Send Test Message** 버튼 클릭
4. 화면 아래 로그 영역에 서버로부터 받은 응답(`response`)이 출력되는지 확인

### 2.6. Prometheus 메트릭 (Browser)

1. 브라우저 접속: `http://localhost/metrics`
2. 화면에 텍스트로 된 메트릭 정보가 출력되는지 확인
3. `Ctrl+F`로 `app_cache_hits_total` 등을 검색하여 수치 변화 확인

### 2.7. Celery Flower 대시보드 (Browser)

1. 브라우저 접속: `http://localhost/flower/`
2. 로그인: `admin` / `change_me`
3. 대시보드 확인:
   - **Workers** 탭: `celery@flask_celery_worker` 상태가 **Online**인지 확인
   - **Tasks** 탭: 이메일 발송 등 비동기 작업 이력 확인

### 2.8. Sentry 에러 트래킹 (Optional)

1. 고의로 에러를 발생시키는 테스트 코드를 작성하거나, DB 연결을 끊고 API를 호출하여 500 에러 유발
2. Sentry 대시보드에서 해당 에러가 수집되었는지 확인

---

## 3. 요약

| 기능          | 테스트 도구    | 주요 확인 사항                   |
| ------------- | -------------- | -------------------------------- |
| **API 기능**  | Swagger UI     | 응답 코드, Body 구조, Auth 동작  |
| **API v2**    | Swagger UI     | HATEOAS 링크, 페이지네이션 헤더  |
| **캐싱**      | Swagger + Logs | 응답 속도, DB 쿼리 발생 여부     |
| **WebSocket** | HTML Client    | 연결 상태, 메시지 수신           |
| **모니터링**  | Browser        | `/metrics`, `/flower/` 접속 여부 |
