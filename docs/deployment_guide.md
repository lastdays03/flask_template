# 배포 가이드 (Deployment Guide)

이 프로젝트는 Docker 및 Docker Compose를 기반으로 배포되도록 설계되었습니다.
본 가이드는 프로덕션 환경 서버에 애플리케이션을 배포하고 운영하는 방법을 설명합니다.

---

## 1. 사전 요구 사항 (Prerequisites)

배포할 서버에는 다음 도구들이 설치되어 있어야 합니다.

- **Docker**: 버전 20.10.x 이상
- **Docker Compose**: 버전 2.x 이상 (Docker Desktop 또는 Plugin 포함 버전)
- **Git**

---

## 2. 배포 절차 (Step-by-Step)

### Step 1. 코드 가져오기
서버에 접속하여 소스 코드를 클론합니다.
```bash
git clone https://github.com/lastdays03/flask_template.git
cd flask_template
```

### Step 2. 환경 변수 설정
프로덕션용 환경 변수 파일을 생성합니다.

```bash
# 예제 파일 복사
cp .env.example .env

# 파일 편집 (프로덕션 비밀키 및 DB 정보 설정)
vim .env
```

**[주의]** `SECRET_KEY`, `JWT_SECRET_KEY`는 반드시 강력한 임의의 문자열로 변경해야 합니다.
```ini
FLASK_ENV=production
SECRET_KEY=very-secure-random-string-must-be-changed
JWT_SECRET_KEY=another-secure-random-string
DATABASE_URL=mysql+pymysql://user:password@db_host:3306/db_name
...
```

### Step 3. 서비스 실행
Docker Compose를 사용하여 모든 서비스(App, Nginx, MariaDB, Redis, Celery)를 실행합니다.

```bash
# 이미지 빌드 및 백그라운드 실행
docker compose up --build -d
```

### Step 4. 배포 확인
```bash
# 컨테이너 상태 확인
docker compose ps

# 로그 확인 (실시간)
docker compose logs -f
```

---

## 3. 모니터링 스택 배포 (Monitoring Stack)

이 프로젝트는 **GlitchTip(Sentry 오픈소스 대안)** 모니터링 스택을 별도로 관리합니다.
앱 배포와 독립적으로 실행되므로 별도의 설정이 필요합니다.

### 2. 별도 실행
`monitoring/` 디렉토리로 이동하여 실행합니다.

```bash
cd monitoring

# 모니터링 전용 .env 설정 (앱 .env와 다름)
cp .env.example .env
vim .env  # GLITCHTIP_SECRET_KEY 설정

# 실행
docker compose up -d
```
- 접속 주소: `http://SERVER_IP:8000`
- 기본 계정 생성: `docker compose exec glitchtip_web ./bin/manage.py createsuperuser`

---

## 4. CI/CD (GitHub Actions)

이 프로젝트는 `.github/workflows/cd.yml` 파일을 통해 배포 자동화를 지원할 준비가 되어 있습니다.

### 자동 배포 활성화 방법
1. GitHub 저장소의 `Settings > Secrets and variables > Actions`에 다음 시크릿을 등록합니다.
    - `SERVER_HOST`: 배포할 서버 IP
    - `SERVER_USER`: SSH 접속 유저 (예: ubuntu)
    - `SERVER_SSH_KEY`: SSH Private Key
2. `cd.yml` 파일에서 주석 처리된 `deploy` Job을 활성화합니다.
3. `main` 브랜치에 푸시되면 자동으로 서버에 접속하여 `git pull` 및 `docker compose up`을 수행합니다.

```yaml
# .github/workflows/cd.yml
deploy:
  needs: build-and-push
  runs-on: ubuntu-latest
  steps:
    - name: Deploy to Server
      uses: appleboy/ssh-action@master
      with:
        # ...
        script: |
          cd ~/flask_template
          git pull origin main
          docker compose up -d --build
```
