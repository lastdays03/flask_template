# 테스트 코드 작성 및 실행 가이드 (Test Code Guide)

이 문서는 `pytest`를 사용하여 프로젝트의 테스트 코드를 작성하고 실행하는 방법을 상세히 설명합니다.

---

## 🧐 왜 테스트 코드를 짜야 하나요? (Why Test?)

1.  **버그 예방**: 코드를 수정했을 때 기존 기능이 고장나는지 즉시 알 수 있습니다.
2.  **문서화 효과**: "이 함수는 이렇게 동작해야 한다"는 것을 코드로 보여줍니다.
3.  **자신감**: 배포할 때 "혹시나..." 하는 불안감을 없애줍니다.

---

## 1. 테스트 환경 설정 (Testing Infrastructure)
(중략...)

## 4. 모의 객체 사용 (Mocking)
(중략...)

---

## 📚 자주 쓰는 검증 메서드 (Common Assertions)

`assert` 문 뒤에 오는 조건이 `False`면 테스트가 실패합니다.

| 검증 내용     | 코드 예시                             | 설명                                 |
| :------------ | :------------------------------------ | :----------------------------------- |
| **값 비교**   | `assert result == 10`                 | 결과가 10이어야 함                   |
| **포함 여부** | `assert "success" in response.json`   | JSON 응답 키에 "success"가 있어야 함 |
| **상태 코드** | `assert response.status_code == 200`  | HTTP 상태 코드가 200이어야 함        |
| **예외 확인** | `with pytest.raises(ValueError): ...` | 실행 시 ValueError가 터져야 성공     |
| **None 체크** | `assert user is not None`             | 유저 객체가 비어있으면 안 됨         |


테스트는 `tests/conftest.py`에 정의된 픽스처(Fixtures)를 통해 안전하고 격리된 환경에서 실행됩니다.
`DeploymentConfig`나 `ProductionConfig`가 아닌 `TestingConfig`가 적용되며, In-Memory SQLite 또는 테스트 전용 DB를 사용할 수 있습니다.

### 주요 픽스처 (Key Fixtures)
- **`app`**: 테스트용 Flask 애플리케이션 인스턴스
- **`client`**: API 요청을 보낼 수 있는 테스트 클라이언트 (브라우저 없이 요청 가능)
- **`db_session`**: 테스트 간 데이터 격리를 보장하는 데이터베이스 세션 (테스트 종료 후 자동 롤백)
- **`auth_headers`**: 로그인된 상태의 인증 헤더를 자동으로 생성해주는 헬퍼

## 2. 테스트 작성 방법 (How to Write Tests)

테스트 파일은 `tests/` 디렉토리 내에 `test_*.py` 형식으로 생성합니다.

### 기본 구조 (Basic Structure)

테스트 파일의 전형적인 구조입니다. `import pytest`는 필수이며, **Given-When-Then** 패턴을 사용하면 가독성이 높아집니다.

```python
import pytest

def test_create_user(client, db_session):
    """
    [설명] 회원가입 성공 시 201 응답과 유저 정보를 반환해야 한다.
    [픽스처]
    - client: API 요청 테스트 클라이언트
    - db_session: 격리된 DB 세션 (테스트 후 자동 롤백)
    """
    
    # 1. Given (준비): 테스트에 필요한 데이터나 상황을 만듭니다.
    payload = {
        "email": "test@example.com",
        "password": "StrongPassword1!",
        "first_name": "Test",
        "last_name": "User"
    }

    # 2. When (실행): 실제로 테스트할 기능(API 호출)을 수행합니다.
    response = client.post("/api/v1/auth/register", json=payload)

    # 3. Then (검증): 결과가 예상대로 나왔는지 확인합니다.
    assert response.status_code == 201, "상태 코드는 201이어야 합니다."
    
    data = response.json
    assert data["success"] is True
    assert data["data"]["email"] == "test@example.com"
```

### 인증이 필요한 API 테스트

`auth_headers` 픽스처를 사용하여 쉽게 인증된 요청을 보낼 수 있습니다.

```python
def test_get_my_profile(client, auth_headers):
    # auth_headers를 헤더에 포함하여 요청
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json["data"]["email"] is not None
```

### 서비스 레이어 단위 테스트 (Unit Test)
API를 거치지 않고 Service 로직만 따로 테스트할 수도 있습니다.

```python
from app.services.user_service import UserService

def test_user_service_create(db_session):
    user = UserService.register_user(
        email="service_test@example.com", 
        password="Pass", 
        first_name="Svc", 
        last_name="Test"
    )
    assert user.id is not None
```

## 3. 테스트 실행 (Running Tests)

프로젝트 루트에서 다음 명령어들을 사용합니다.

```bash
# 1. 전체 테스트 실행
pytest

# 2. 자세한 출력 보기 (-v)
pytest -v

# 3. 특정 파일만 실행
pytest tests/test_auth.py

# 4. 특정 함수만 실행 (-k 키워드)
pytest -k "test_login"

# 5. 실패한 첫 번째 테스트에서 멈추기 (-x)
pytest -x
```

### 커버리지 확인 (Code Coverage)
얼마나 많은 코드가 테스트되었는지 확인합니다.

```bash
# 커버리지 리포트 생성 (터미널 출력)
pytest --cov=app tests/

# HTML 리포트 생성 (htmlcov/index.html 파일 열기)
pytest --cov=app --cov-report=html tests/
```

## 4. 모의 객체 사용 (Mocking)

외부 서비스(이메일 발송, 결제 등)나 무거운 작업은 `unittest.mock`을 사용하여 대체(Mocking)합니다.

```python
from unittest.mock import patch

def test_send_email():
    with patch("app.utils.email.send_email") as mock_email:
        # 이메일 발송 로직 실행
        result = do_something_that_sends_email()
        
        # 실제 발송 대신 Mock 함수가 호출되었는지 확인
        assert mock_email.called
```
