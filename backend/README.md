# Backend Setup

## 1. Environment

루트 `.env.example`을 복사해 `.env`를 생성하고 DB 접속 정보를 설정합니다.

- 로컬 실행: `DB_HOST=localhost`
- Docker 실행: `DB_HOST_DOCKER=mariadb`

## 2. Run

프로젝트 루트에서 실행:

```bash
docker compose up -d --build
```

## 3. API specification

FastAPI generates the API specification from implemented routes and Pydantic
models. With the backend running, use the following endpoints:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON for frontend integration: `http://localhost:8000/openapi.json`

Development-only APIs, including `POST /dev/test-auth`, are included only when
`APP_ENV=development`. Its OpenAPI definition explicitly documents `200` and
`500` responses.

## 4. Database Migration

`backend/` 디렉터리에서 실행합니다. MariaDB가 실행 중이어야 합니다.

```bash
# 마이그레이션 파일 생성
uv run alembic revision --autogenerate -m "describe change"

# DB 스키마 적용
uv run alembic upgrade head
```

마이그레이션 파일은 `alembic/versions/`에 생성되며, 적용 전 변경 사항을 검토합니다.

# 기술적 의사결정
## 1. 동기식 DB 연결 방식 선택

**선택: 동기식 SQLAlchemy + PyMySQL**

- **선택 이유:** 현재 서비스는 회원 인증, 채팅 기록 저장·조회 등 짧은 DB 작업이 중심이며, 대규모 동시 요청이 예상되지 않음. 동기 방식으로도 FastAPI의 스레드풀을 통해 동시 요청을 처리할 수 있어 구현이 단순한 동기식을 선택함.
- **고려한 대안:** 비동기 방식(SQLAlchemy AsyncSession + 비동기 DB 드라이버)
- **트레이드오프:** DB 응답 대기 중 스레드를 점유하므로, 동시 요청이 많아지면 스레드 자원이 병목이 될 수 있음.
- **결정:** 현재 예상 트래픽 대비 비동기 방식의 이점이 크지 않다고 판단하여 동기식을 채택함.

## 2. SQLAlchemy 선택

**선택: SQLAlchemy 2.x ORM**

- **선택 이유:** 사용자·채팅방·메시지 간 FK 관계를 객체로 매핑하고, 반복적인 SQL 작성과 결과 변환 코드를 줄일 수 있음. 또한 DB 모델과 Pydantic API 스키마를 분리하여 관리할 수 있음.
- **고려한 대안:**
  - **PyMySQL 직접 사용:** SQL을 직접 제어할 수 있지만, CRUD 및 관계 데이터 처리 시 반복 코드가 증가함.
  - **SQLModel:** 모델 정의를 간소화할 수 있지만, DB 모델과 API 스키마를 분리하는 현재 구조에서는 통합의 이점이 상대적으로 작음.
- **트레이드오프:** ORM 학습과 별도 스키마 정의가 필요하며, 복잡한 쿼리는 생성 SQL과 성능을 확인해야 함.
- **결정:** 관계형 데이터 관리와 DB·API 계층의 명확한 분리를 위해 SQLAlchemy를 채택함.

## 3. Alembic 선택

선택: Alembic을 이용한 DB 스키마 버전 관리

선택 이유: SQLAlchemy 모델의 변경 사항을 바탕으로 마이그레이션 파일을 생성하고, DB 스키마 변경 이력을 관리할 수 있음.

고려한 대안: 수동 DDL 작성, Base.metadata.create_all()

트레이드오프: 마이그레이션 파일 생성·검토·적용 과정이 필요하며, 팀원 간 revision 충돌을 관리해야 함.

결정: 여러 개발자가 협업하는 환경에서 DB 스키마 변경 이력을 공유하고 재현하기 위해 채택함.
