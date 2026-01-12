# Flask Production REST API Template

프로덕션 환경을 위한 Flask REST API 백엔드 템플릿입니다. JWT 인증, Celery 비동기 작업, Redis 캐싱, WebSocket 실시간 통신, 모니터링 시스템(Prometheus, Sentry) 및 Docker 배포 환경을 포함하고 있습니다.

## 주요 기능 (Key Features)

- **Flask 3.x** (Application Factory 패턴 적용)
- **API 버전 관리**: Blueprint 기반 v1/v2 API 구조 및 마이그레이션 전략
- **Flask-RESTX**: Swagger/OpenAPI 문서 자동화
- **인증 (Authentication)**:
  - JWT Access/Refresh Token 기반 인증
  - **Google OAuth2** 소셜 로그인
- **데이터베이스**: SQLAlchemy ORM (MySQL 8.0)
- **비동기 작업**: Celery 5.3 + Redis Broker
- **캐싱 & 큐**: Service 레벨 **Redis Caching** (@cached 데코레이터) 및 메시지 큐
- **실시간 통신**: **Flask-SocketIO** 기반 WebSocket 지원 (알림 등)
- **모니터링 & 관측성**:
  - **Prometheus** 메트릭 수집 (/metrics)
  - **Sentry** 에러 트래킹 연동
  - **Celery Flower** 대시보드 (작업 모니터링)
- **고급 페이지네이션**: HATEOAS 링크 및 RFC 5988 Link Header 지원
- **CI/CD**: GitHub Actions (테스트, 린팅, 도커 빌드)
- **배포**: Docker & Docker Compose (Nginx 리버스 프록시 포함)

## 기술 스택 (Tech Stack)

- **Backend**: Python 3.12, Flask 3.0
- **API**: Flask-RESTX 1.3
- **Database**: MySQL 8.0
- **Cache/Queue**: Redis 7
- **Worker**: Celery 5.3
- **Real-time**: Flask-SocketIO 5.3, Eventlet
- **Monitoring**: Prometheus Client, Sentry SDK, Flower
- **Server**: Gunicorn, Nginx
- **Testing**: pytest

## 프로젝트 구조 (Project Structure)

```text
flask_template/
├── .github/
│   └── workflows/           # CI/CD (ci.yml, cd.yml)
├── app/
│   ├── __init__.py          # 앱 팩토리 (Sentry, Metrics, Blueprint 설정)
│   ├── api/                 # API 엔드포인트
│   │   ├── v1/              # API v1 (Auth, User 등)
│   │   └── v2/              # API v2 (개선된 User API)
│   ├── events/              # WebSocket 이벤트 핸들러
│   ├── middleware/          # 미들웨어 (버전 Deprecation 등)
│   ├── models/              # DB 모델
│   ├── schemas/             # Pydantic/Marshmallow 스키마
│   ├── services/            # 비즈니스 로직 (Service Layer)
│   ├── tasks/               # Celery 비동기 작업
│   └── utils/               # 유틸리티 (Cache, Logger, Metrics, Pagination)
├── docker/                  # Docker 설정 (Dockerfile, Nginx)
├── docs/                    # 프로젝트 문서 (마이그레이션 가이드 등)
├── tests/                   # 테스트 스위트
├── flower_config.py         # Flower 설정 파일
├── docker-compose.yml       # Docker Compose 설정
├── requirements.txt         # 의존성 패키지
└── wsgi.py                  # WSGI 진입점
```

## 시작하기 (Quick Start)

### 1. 로컬 개발 환경 설정

```bash
# 레포지토리 클론
git clone <repository-url>
cd flask_template

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 설정을 수정합니다.

```bash
cp .env.example .env
```

**주요 환경 변수:**
- `SENTRY_DSN`: Sentry 프로젝트 DSN
- `GOOGLE_CLIENT_ID` / `SECRET`: 구글 로그인 연동 시 필요
- `FLOWER_USER` / `PASSWORD`: Celery 모니터링 대시보드 접근 계정

### 3. 서비스 실행 (Docker)

MySQL, Redis 등 인프라 서비스를 Docker로 실행합니다.

```bash
docker-compose up -d mysql redis
```

### 4. 데이터베이스 초기화

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. 서버 실행

**Flask 개발 서버:**
```bash
flask run
```

**Celery 워커:**
```bash
celery -A celery_worker.celery worker --loglevel=info
```

**Celery Flower 대시보드 (선택):**
```bash
celery -A celery_worker.celery flower --conf=flower_config
```

---

## API 사용법 (API Documentation)

서버 실행 후 브라우저에서 아래 주소로 접속하여 API 문서를 확인할 수 있습니다.

- **Swagger UI (v1)**: [http://localhost:5000/api/v1/docs](http://localhost:5000/api/v1/docs)
- **Swagger UI (v2)**: [http://localhost:5000/api/v2/docs](http://localhost:5000/api/v2/docs)
- **API Root**: [http://localhost:5000/api](http://localhost:5000/api) (버전 정보 및 Deprecation 상태 확인)

### 주요 엔드포인트

**Authentication (v1)**
- `POST /api/v1/auth/register`: 회원가입
- `POST /api/v1/auth/login`: 로그인
- `GET /api/v1/auth/google/login`: 구글 소셜 로그인

**Users (v1 & v2)**
- `GET /api/v1/users`: 사용자 목록 (v1)
  - 응답: `{ "users": [...], "total": 100, "page": 1 }`
- `GET /api/v2/users`: 사용자 목록 (v2 - 권장)
  - 응답: HATEOAS 구조 및 풍부한 메타데이터 포함
  ```json
  {
    "data": [...],
    "meta": { "page": 1, "per_page": 10, "total": 100 },
    "links": { "self": "...", "next": "..." }
  }
  ```
  - 헤더: `Link` (RFC 5988 페이지네이션) 포함

**Monitoring**
- `GET /api/v1/health`: 헬스 체크
- `GET /metrics`: Prometheus 메트릭

## 배포 (Deployment)

Docker Compose를 사용하여 전체 스택(App, Worker, Flower, Nginx, DB, Redis)을 한 번에 배포할 수 있습니다.

```bash
# 서비스 빌드 및 실행
docker-compose up --build -d

# 로그 확인
docker-compose logs -f
```

- **API Server**: http://localhost (Nginx 80포트)
- **Flower Dashboard**: http://localhost/flower/ (Celery 모니터링)

## 테스트 (Testing)

GitHub Actions CI 파이프라인이 구성되어 있습니다. 로컬에서 테스트를 실행하려면:

```bash
# 전체 테스트 실행
pytest -v

# 커버리지 리포트
pytest --cov=app tests/
```

## 모니터링 및 관측성

1. **Prometheus**: `/metrics` 엔드포인트를 통해 Flask 및 시스템 메트릭을 노출합니다.
2. **Sentry / GlitchTip**: 애플리케이션 예외 발생 시 자동으로 에러 리포트를 전송합니다.
   - **GlitchTip Self-Hosted 가이드**: [docs/USAGE_GLITCHTIP.md](docs/USAGE_GLITCHTIP.md) (Docker Compose 분리 배포)
3. **Flower**: `http://localhost/flower/`에서 비동기 작업 처리 현황을 실시간으로 모니터링할 수 있습니다.

## WebSocket 실시간 통신

- 클라이언트: `examples/websocket_client.html`
- 기능:
  - JWT 인증 기반 연결
  - 실시간 메시지 송수신 (ACK 지원)
  - 송신(Sent) 및 수신(Received) 로그 UI 분리

## 라이선스 (License)

MIT License
