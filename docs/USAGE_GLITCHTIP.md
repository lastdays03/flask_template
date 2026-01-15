# GlitchTip (Self-Hosted Sentry) 사용 가이드

이 가이드는 로컬 환경에서 독립된 GlitchTip 모니터링 스택을 구축하고, Flask 애플리케이션과 연동하는 방법을 설명합니다.

## 1. 개요 (Architecture)

GlitchTip은 Sentry 오픈소스 호환 구현체로, 애플리케이션의 에러를 수집하고 추적합니다.
이 프로젝트에서는 `/monitoring` 디렉토리에 별도의 Docker Compose 스택으로 구성되어, 메인 애플리케이션과 독립적으로 실행됩니다.

- **접속 주소**: [http://localhost:8000](http://localhost:8000)
- **구성 요소**: GlitchTip Web, Worker, PostgreSQL, Redis

## 2. 설치 및 실행 (Installation)

### 2.1 스택 실행
먼저 `monitoring` 디렉토리로 이동하여 컨테이너를 실행합니다.

```bash
cd monitoring
docker compose up -d
```

### 2.2 접속 확인
브라우저에서 `http://localhost:8000`에 접속하여 로그인 화면이 뜨는지 확인합니다.

---

## 3. 초기 설정 (Initial Setup)

GlitchTip을 처음 실행하면 관리자(Superuser) 계정 생성이 필요합니다.

### 3.1 관리자 계정 생성 (터미널)
웹 화면에서 가입할 수도 있지만, 터미널 명령어로 Superuser를 생성하는 것이 확실합니다.

먼저 데이터베이스 마이그레이션을 수행하여 테이블을 생성해야 합니다.

```bash
# monitoring 폴더에서 실행
docker compose run --rm monitoring_web ./manage.py migrate
```

그 다음, 관리자 계정을 생성합니다.

```bash
# monitoring 폴더에서 실행
docker compose run --rm monitoring_web ./manage.py createsuperuser
# Email: admin@localhost
# Password: (임의 설정)
```

### 3.2 프로젝트 생성 (웹 UI)
1. 생성한 계정으로 로그인합니다.
2. **Organizations** -> **Create New Organization** (예: `MyOrg`)
3. **Projects** -> **Create New Project** (예: `flask-api`)
4. 플랫폼 유형으로 **Python** 또는 **Flask**를 선택합니다.
5. 생성 완료 후 **DSN (Data Source Name)** 주소를 복사합니다.
    - 예: `http://<key>@localhost:8000/1`

---

## 4. Flask 애플리케이션 연동

### 4.1 환경 변수 설정
메인 프로젝트의 `.env` 파일을 열고 `SENTRY_DSN` 값을 수정합니다.

```bash
# .env 파일
SENTRY_DSN=http://<복사한_public_key>@localhost:8000/1
```

> **주의**: Docker 컨테이너(Flask App)에서 호스트(GlitchTip)로 접속해야 하므로, `localhost` 대신 `host.docker.internal`을 사용해야 할 수 있습니다.
> 예: `http://abc...@host.docker.internal:8000/1` (Mac/Windows Docker Desktop 기준)

### 4.2 앱 재시작
변경 사항을 적용하기 위해 Flask 앱을 재시작합니다.

```bash
# 프로젝트 루트에서
docker compose up -d app
```

---

## 5. 테스팅 (Verification)

### 5.1 에러 발생시키기
Flask 앱에서 고의로 500 에러를 유발합니다. (테스트 코드를 작성하거나, 임시로 코드에 `1/0` 추가)

### 5.2 모니터링 확인
GlitchTip 대시보드(`http://localhost:8000/organizations/myorg/issues/`)에서 해당 에러가 수집되었는지 확인합니다.
