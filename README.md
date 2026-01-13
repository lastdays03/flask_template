# Flask Production REST API Template

프로덕션 환경을 위한 Flask REST API 백엔드 템플릿입니다. JWT 인증, Celery 비동기 작업, Redis 캐싱, WebSocket 실시간 통신, 모니터링 시스템(Prometheus, Sentry) 및 Docker 배포 환경을 포함하고 있습니다.

## 주요 기능 (Key Features)

- **Flask 3.x** (Application Factory 패턴 적용)
- **API 버전 관리**: Blueprint 기반 v1/v2 API 구조 및 마이그레이션 전략
- **Flask-RESTX**: Swagger/OpenAPI 문서 자동화
- **인증 (Authentication)**:
  - JWT Access/Refresh Token 기반 인증 (Redis Blacklist 연동 로그아웃 지원)
  - **Google OAuth2** 소셜 로그인
  - **강력한 비밀번호 정책**: 최소 8자, 대/소문자, 숫자, 특수문자 포함 강제
- **데이터베이스**: SQLAlchemy ORM (MariaDB 10.8)
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
- **Database**: MariaDB 10.8
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


## 📚 문서 (Documentation)

더 자세한 내용은 아래 가이드 문서를 참고하세요.

- **[개발 가이드 (Development Guide)](docs/development_guide.md)**: 아키텍처, 구현 패턴, 테스트 방법
- **[배포 가이드 (Deployment Guide)](docs/deployment_guide.md)**: 서버 배포, 환경 설정, 모니터링 스택 구축
- **[DB 사용 가이드 (Database Guide)](docs/database_guide.md)**: SQLAlchemy ORM 사용법 (CRUD, Transaction)
- **[테스트 코드 가이드 (Test Code Guide)](docs/test_code_guide.md)**: Pytest 작성 및 실행 방법
- **[기능별 테스트 가이드 (Manual Testing)](docs/testing_guide.md)**: Docker & Swagger UI 기반 수동 테스트
- **[Swagger 가이드 (API Guide)](docs/development_guide.md#step-4-컨트롤러-구현-및-swagger-문서화-controller--swagger-docs)**: API 명세 작성법 (개발 가이드에 포함됨)

## 시작하기 (Quick Start)

### 1. 로컬 개발 환경 설정

```bash
# 레포지토리 클론
git clone https://github.com/lastdays03/flask_template.git
cd flask_template

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치 (개발 툴 포함)
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 설정을 수정합니다.

```bash
cp .env.example .env
```

**[필수 변경]**
- `SECRET_KEY`, `JWT_SECRET_KEY`: 보안을 위해 변경 필요
- `GOOGLE_CLIENT_ID`: 소셜 로그인 미사용 시 무시 가능

### 3. 인프라 실행 (Docker)

로컬 개발 시 DB와 Redis는 Docker로 실행하는 것이 편리합니다.

```bash
# MariaDB 및 Redis 실행
docker compose up -d mariadb redis
```

> **참고**: 전체 스택(Nginx, Celery 등 포함)을 실행하려면 `docker compose up -d --build`를 사용하세요.

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

**Celery 워커 & Flower (필요 시 별도 터미널):**
```bash
# 워커 실행
celery -A celery_worker.celery worker --loglevel=info

# 모니터링 대시보드 (http://localhost:5555)
celery -A celery_worker.celery flower --conf=flower_config
```

### 6. 모니터링 스택 (선택)
GlitchTip(Sentry)은 별도의 독립된 스택으로 관리됩니다.

```bash
cd monitoring
docker compose up -d
```
- 자세한 내용은 [배포 가이드](docs/deployment_guide.md)를 참고하세요.

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
- `POST /api/v1/auth/logout`: 로그아웃 (토큰 무효화)

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
docker compose up --build -d

# 로그 확인
docker compose logs -f
```

- **API Server**: http://localhost (Nginx 80포트)
- **Flower Dashboard**: http://localhost/flower/ (Celery 모니터링)

## 개발 가이드 (Development Guide)
 
 **코드 품질 관리 (Linting & Formatting)**
 
 본 프로젝트는 CI 파이프라인에서 엄격한 코드 품질 검사를 수행합니다. Pull Request 제출 전 반드시 로컬에서 린트를 통과해야 합니다.
 
 1. **의존성 패키지 설치**
    ```bash
    # 앱 실행 및 개발 툴 모두 설치
    pip install -r requirements.txt -r requirements-dev.txt
    ```
 
 2. **코드 포맷팅 (Black)**
    ```bash
    # 포맷팅 실행 (파일 자동 수정)
    black .
    ```
 
 3. **정적 분석 (Pylint)**
    ```bash
    # 린트 검사 실행
    pylint app
    ```
    - **CI 통과 기준**: 점수 **9.0** 이상
    - *참고: 로컬 환경 구성에 따라 `import-error`로 점수가 낮게 나올 수 있습니다. 이 경우 소스 코드의 로직/스타일 경고를 우선적으로 해결해 주세요.*

 4. **Git Hook 설정 (Pre-push Lint)**
    
    Git 서버에 푸시하기 전에 자동으로 코드를 검사하도록 훅을 설치합니다.
    
    ```bash
    # pre-commit 설치 및 훅 설정
    pip install -r requirements-dev.txt
    pre-commit install --hook-type pre-push
    ```
    
    설정이 완료되면 `git push` 실행 시 자동으로 **Test(Pytest)** 및 **Lint(Black, Flake8)** 가 실행됩니다. 검사에 실패하면 푸시가 거부됩니다.
 
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

## 🤝 협업 가이드 (Collaboration)

우리 팀은 **Git-Flow** 전략과 **Conventional Commits**를 따릅니다.

### 1. Git 브랜치 전략
- **`main`**: 언제든 배포 가능한 안정 버전. (직접 push 금지, PR로만 병합)
- **`develop`**: 개발 중인 기능이 모이는 통합 브랜치.
- **`feature/*`**: 개별 기능을 개발하는 브랜치.
    - **명명 규칙**: GitHub Issue 번호와 제목을 조합 (예: `feature/1-login-page`)

### 2. 커밋 메시지 규칙 (Conventional Commits)
커밋 메시지는 `타입: 제목` 형식을 따릅니다.

- **feat**: 새로운 기능 추가 (예: `feat: 회원가입 API 구현`)
- **fix**: 버그 수정
- **docs**: 문서 수정 (README, Docstring 등)
- **refactor**: 코드 리팩토링 (기능 변경 없음)
- **test**: 테스트 코드 추가/수정
- **chore**: 설정 변경, 패키지 매니저 등

---

## 라이선스 (License)

MIT License
