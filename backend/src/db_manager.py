"""db_manager 모듈: SQLAlchemy ORM 모델 + CRUD (DB-001~005, ENG-006)."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

from src.config import settings

# ---------------------------------------------------------------------------
# Engine / Session
# ---------------------------------------------------------------------------

engine = create_engine(
    settings.db_url,
    connect_args={"check_same_thread": False},  # SQLite 멀티스레드 허용
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,  # 세션 종료 후에도 속성 접근 가능
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# ORM Base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# DB-001: UploadedFile 모델
# ---------------------------------------------------------------------------


class UploadedFile(Base):
    """업로드 파일 정보 (DB-001)."""

    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # pending / processing / done / error
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)


# ---------------------------------------------------------------------------
# DB 초기화
# ---------------------------------------------------------------------------


def init_db() -> None:
    """테이블 생성. 앱 기동 시 1회 호출."""
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# DB-001: 파일 정보 CRUD
# ---------------------------------------------------------------------------


def save_file_info(
    filename: str,
    file_path: str,
    row_count: int | None = None,
) -> UploadedFile:
    with get_session() as session:
        file = UploadedFile(filename=filename, file_path=file_path, row_count=row_count)
        session.add(file)
        session.flush()
        session.refresh(file)
        return file


def update_file_status(file_id: int, status: str) -> None:
    with get_session() as session:
        file = session.get(UploadedFile, file_id)
        if file:
            file.analysis_status = status


def get_file_info(file_id: int) -> UploadedFile | None:
    with get_session() as session:
        return session.get(UploadedFile, file_id)
