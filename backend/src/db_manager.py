"""db_manager 모듈: SQLAlchemy ORM 모델 + CRUD (DB-001~005, ENG-006)."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
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

    results: Mapped[list[AnalysisResult]] = relationship(
        "AnalysisResult", back_populates="file", cascade="all, delete-orphan"
    )


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


# ---------------------------------------------------------------------------
# DB-002: AnalysisResult 모델
# ---------------------------------------------------------------------------


class AnalysisResult(Base):
    """분석 결과 (DB-002)."""

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[int] = mapped_column(Integer, ForeignKey("uploaded_files.id"), nullable=False)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)  # PASS / 관리필요 / FAIL
    anomalies: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    trip_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    report_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    file: Mapped[UploadedFile] = relationship("UploadedFile", back_populates="results")


# ---------------------------------------------------------------------------
# DB-002: 분석 결과 CRUD
# ---------------------------------------------------------------------------


def save_analysis_result(
    file_id: int,
    verdict: str,
    anomalies: dict | None = None,
    trip_info: dict | None = None,
    report_text: str | None = None,
) -> AnalysisResult:
    with get_session() as session:
        result = AnalysisResult(
            file_id=file_id,
            verdict=verdict,
            anomalies=anomalies,
            trip_info=trip_info,
            report_text=report_text,
        )
        session.add(result)
        session.flush()
        session.refresh(result)
        return result


def get_analysis_history(limit: int = 50) -> list[dict]:
    """/api/history 응답용 — main.py가 직접 반환할 수 있는 dict 리스트."""
    with get_session() as session:
        rows = (
            session.query(AnalysisResult, UploadedFile)
            .join(UploadedFile, AnalysisResult.file_id == UploadedFile.id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "일시": r.created_at.strftime("%Y-%m-%d %H:%M"),
                "파일명": f.filename,
                "행수": f.row_count,
                "판정": r.verdict,
            }
            for r, f in rows
        ]


def get_analysis_result(file_id: int) -> AnalysisResult | None:
    """특정 파일의 최신 분석 결과 조회."""
    with get_session() as session:
        return (
            session.query(AnalysisResult)
            .filter(AnalysisResult.file_id == file_id)
            .order_by(AnalysisResult.created_at.desc())
            .first()
        )
