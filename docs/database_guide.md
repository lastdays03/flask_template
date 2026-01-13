# SQLAlchemy ORM 사용 가이드 (Database Guide)

이 문서는 Flask 프로젝트에서 **SQLAlchemy ORM**을 사용하여 데이터베이스를 다루는 방법을 설명합니다.

## 1. 모델 정의 (Model Definition)

모든 모델은 `app.models.base.BaseModel`을 상속받아야 합니다. 이 클래스는 `id`, `created_at`, `updated_at` 필드와 `save()`, `delete()`, `to_dict()` 메서드를 기본 제공합니다.

```python
from app.extensions import db
from app.models.base import BaseModel

class Product(BaseModel):
    __tablename__ = "products"

    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    # 관계 정의 (Relationship)
    user = db.relationship("User", backref=db.backref("products", lazy=True))
```

## 2. 모델 설계 베스트 프랙티스 (Model Design Best Practices)

실무에서 자주 사용하는 설계 패턴과 규칙입니다.

### 2.1 명명 규칙 (Naming Convention)
| 구분            | 규칙                 | 예시                      | 비고             |
| :-------------- | :------------------- | :------------------------ | :--------------- |
| **테이블**      | 복수형, snake_case   | `users`, `order_items`    |                  |
| **컬럼**        | snake_case           | `first_name`, `is_active` |                  |
| **Foreign Key** | `단수형_테이블명_id` | `user_id`, `product_id`   | 명확한 관계 표현 |

### 2.2 관계 설정 (Relationship Patterns)

**1:N (일대다) - 가장 흔한 패턴**
- 예: 한 명의 유저(User)가 여러 개의 주문(Order)을 가짐

```python
class User(BaseModel):
    # ...
    # 1쪽에서 N쪽을 접근할 때 (user.orders)
    orders = db.relationship("Order", backref="user", lazy=True)

class Order(BaseModel):
    # ...
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
```

**N:M (다대다) - 중간 테이블 활용**
- 예: 학생(Student)과 수업(Class)의 관계. `student_class`라는 연결 테이블이 필요합니다.

### 2.3 인덱스 전략 (Indexing)
검색 성능을 높이기 위해 `index=True`를 사용합니다. 단, 쓰기 성능이 약간 저하되므로 조회 빈도가 높은 컬럼에만 적용합니다.

```python
class User(BaseModel):
    # 이메일로 회원을 자주 찾는다면 인덱스 필수
    email = db.Column(db.String(120), unique=True, index=True)
    
    # 복합 인덱스 (두 개 이상의 컬럼 조합)
    __table_args__ = (
        db.Index('idx_name_email', 'name', 'email'),
    )
```

### 2.4 모델 파일 관리 전략 (File Structure)

모델이 늘어날수록 파일을 어떻게 나눌지 고민됩니다. 본 프로젝트는 **도메인(기능) 단위 그룹화**를 권장합니다.

**1. 도메인 단위 그룹화 (추천)**
밀접하게 연관된 모델들을 하나의 파일로 묶습니다.
- `user.py`: `User`, `UserRole`, `Profile` (회원 관련 전체)
- `product.py`: `Product`, `Category`, `ProductTag` (상품 관련 전체)
- `order.py`: `Order`, `OrderItem`, `Payment` (주문 관련 전체)

**장점**:
- 파일 개수가 적당하게 유지됩니다.
- 같은 도메인 내의 모델끼리는 `import` 없이도 참조가 쉬워 **순환 참조(Circular Import)** 문제를 피하기 좋습니다.

**✅ 순환 참조 방지 꿀팁**
다른 파일에 있는 모델과 관계(Relationship)를 맺을 때는 클래스 대신 **"문자열"**을 사용하세요.
```python
# app/models/order.py
class Order(BaseModel):
    # User 클래스를 import 하지 않고 문자열로 참조
    user = db.relationship("User", backref="orders") 
    
    # ForeignKey도 문자열 테이블명 사용
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
```

### 2.5 소프트 삭제 (Soft Delete)
데이터를 실제로 삭제하지 않고 숨김 처리하는 패턴입니다. `deleted_at` 필드를 추가하여 관리합니다.

```python
from datetime import datetime

class User(BaseModel):
    # ...
    deleted_at = db.Column(db.DateTime, nullable=True)

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()
        self.save()
```
> **Tip**: 조회 시 항상 `filter(User.deleted_at == None)` 조건을 걸어야 합니다.

## 3. CRUD 작업

### 생성 (Create)
`BaseModel`의 `save()` 메서드를 사용하면 `db.session.add()`와 `commit()`을 자동으로 처리합니다.

```python
# 방법 1: 생성자 사용
product = Product(name="MacBook", price=2000000)
product.save()

# 방법 2: 쿼리 후 저장
user = User.query.get(1)
product = Product(name="Mouse", user=user)
product.save()
```

### 조회 (Read)
`Model.query` 객체를 사용합니다.

```python
# ID로 조회 (Primary Key)
product = Product.query.get(1)
# SQLAlchemy 2.0 스타일 (Legacy Warning 방지)
product = db.session.get(Product, 1)

# 조건 조회
products = Product.query.filter_by(name="MacBook").all()
product = Product.query.filter(Product.price > 1000).first()

# 정렬 및 제한
recent_products = Product.query.order_by(Product.created_at.desc()).limit(10).all()

# 페이지네이션 (Pagination)
page = Product.query.paginate(page=1, per_page=10, error_out=False)
items = page.items
total = page.total
```

### 수정 (Update)
객체의 속성을 변경하고 `db.session.commit()`을 호출합니다. `save()`를 호출해도 됩니다.

```python
product = Product.query.get(1)
product.price = 1500000
product.save() # 내부적으로 commit() 호출
```

### 삭제 (Delete)
`BaseModel`의 `delete()` 메서드를 사용합니다.

```python
product = Product.query.get(1)
product.delete() # 내부적으로 db.session.delete(self) 및 commit() 호출
```

## 4. 트랜잭션 관리 (Transactions)

여러 작업을 하나의 트랜잭션으로 묶을 때는 `db.session`을 직접 제어하거나 `save()`를 사용하지 않고 명시적으로 커밋합니다.

```python
try:
    user = User(email="new@test.com")
    db.session.add(user)
    
    profile = Profile(user=user, bio="Hello")
    db.session.add(profile)
    
    db.session.commit() # 여기서 트랜잭션 확정
except Exception:
    db.session.rollback() # 에러 발생 시 롤백
    raise
```

## 5. 마이그레이션 (Flask-Migrate)

모델 코드가 변경되면 반드시 마이그레이션 파일을 생성하고 DB에 적용해야 합니다.

```bash
# 1. 마이그레이션 파일 생성 (변경사항 감지)
flask db migrate -m "Add product model"

# 2. 변경사항 DB 적용
flask db upgrade

# 3. 마이그레이션 취소 (필요 시)
flask db downgrade
```

## 6. 자주 쓰는 메서드 모음 (Cheat Sheet)

초급 개발자가 가장 많이 사용하는 ORM 패턴입니다.

| 작업          | 코드 예시                                       | 설명                               |
| :------------ | :---------------------------------------------- | :--------------------------------- |
| **단건 조회** | `User.query.get(1)`                             | PK로 검색. 없으면 `None` 반환      |
| **조건 검색** | `User.query.filter_by(email="a@b.com").first()` | 조건에 맞는 첫 번째 데이터         |
| **전체 검색** | `User.query.all()`                              | 모든 데이터 리스트로 반환          |
| **개수 세기** | `User.query.count()`                            | 데이터 개수 반환                   |
| **저장/수정** | `user.save()`                                   | 변경사항을 DB에 저장 (Commit 포함) |
| **삭제**      | `user.delete()`                                 | 데이터를 DB에서 삭제 (Commit 포함) |

---

## ❓ DB 디버깅 팁

### Q. 실제 실행되는 SQL을 보고 싶어요.
`config.py` 또는 로컬 설정에서 `SQLALCHEMY_ECHO = True`로 설정하면 콘솔에 모든 SQL 로그가 출력됩니다.

```python
# app/config.py
class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_ECHO = True  # SQL 로그 출력 활성화
```

### Q. 'Detached InstanceError'가 뭐죠?
DB 세션이 닫힌 후에 객체 속성에 접근하려 할 때 발생합니다. 보통 트랜잭션 범위 밖에서 지연 로딩(Lazy Loading)된 관계 필드를 읽으려 할 때 생깁니다.
**해결법**: 쿼리 시 `.options(joinedload(User.posts))`를 사용하거나, 필요한 데이터를 미리 DTO로 변환하세요.
