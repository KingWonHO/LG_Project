"""db_manager 모듈: SQLAlchemy ORM 모델 + CRUD (DB-001~005, ENG-006)."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

from sqlalchemy import (
    DateTime,
    Float,
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


# ---------------------------------------------------------------------------
# DB-003: TripCode 모델
# ---------------------------------------------------------------------------


class TripCode(Base):
    """Trip Code 정의 (DB-003)."""

    __tablename__ = "trip_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_no: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    trip_key: Mapped[str] = mapped_column(String(100), nullable=False)
    trip_name_ko: Mapped[str] = mapped_column(String(100), nullable=False)
    summary_ko: Mapped[str] = mapped_column(Text, nullable=False)
    restart_delay_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    solution: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# DB-003: Trip Code CRUD
# ---------------------------------------------------------------------------


def upsert_trip_code(
    trip_no: int,
    trip_key: str,
    trip_name_ko: str,
    summary_ko: str,
    restart_delay_s: int | None = None,
    solution: dict | None = None,
) -> TripCode:
    with get_session() as session:
        existing = session.query(TripCode).filter(TripCode.trip_no == trip_no).first()
        if existing:
            existing.trip_key = trip_key
            existing.trip_name_ko = trip_name_ko
            existing.summary_ko = summary_ko
            existing.restart_delay_s = restart_delay_s
            existing.solution = solution
            existing.updated_at = datetime.utcnow()
            session.flush()
            session.refresh(existing)
            return existing
        new = TripCode(
            trip_no=trip_no,
            trip_key=trip_key,
            trip_name_ko=trip_name_ko,
            summary_ko=summary_ko,
            restart_delay_s=restart_delay_s,
            solution=solution,
        )
        session.add(new)
        session.flush()
        session.refresh(new)
        return new


def get_all_trip_codes() -> list[TripCode]:
    with get_session() as session:
        return session.query(TripCode).order_by(TripCode.trip_no).all()


def get_trip_code(trip_no: int) -> TripCode | None:
    with get_session() as session:
        return session.query(TripCode).filter(TripCode.trip_no == trip_no).first()


def seed_trip_codes_from_json(json_path: str | Path) -> int:
    """Trip_case.json에서 초기 데이터 삽입. 이미 존재하면 upsert. 삽입 건수 반환."""
    import json
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    count = 0
    for trip in data.get("trips", []):
        upsert_trip_code(
            trip_no=trip["trip_no"],
            trip_key=trip["trip_key"],
            trip_name_ko=trip["trip_name_ko"],
            summary_ko=trip["summary_ko"],
            restart_delay_s=trip.get("restart_delay_s"),
            solution=trip.get("solution"),
        )
        count += 1
    return count


# ---------------------------------------------------------------------------
# DB-004: Baseline 모델
# ---------------------------------------------------------------------------


class Baseline(Base):
    """feature별 정상 기준값 (DB-004)."""

    __tablename__ = "baselines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    min_val: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_val: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# DB-004: Baseline CRUD
# ---------------------------------------------------------------------------


def upsert_baseline(
    feature_name: str,
    min_val: float | None = None,
    max_val: float | None = None,
    unit: str | None = None,
) -> Baseline:
    with get_session() as session:
        existing = session.query(Baseline).filter(Baseline.feature_name == feature_name).first()
        if existing:
            existing.min_val = min_val
            existing.max_val = max_val
            existing.unit = unit
            existing.updated_at = datetime.utcnow()
            session.flush()
            session.refresh(existing)
            return existing
        new = Baseline(feature_name=feature_name, min_val=min_val, max_val=max_val, unit=unit)
        session.add(new)
        session.flush()
        session.refresh(new)
        return new


def get_baseline(feature_name: str) -> Baseline | None:
    with get_session() as session:
        return session.query(Baseline).filter(Baseline.feature_name == feature_name).first()


def get_all_baselines() -> list[Baseline]:
    with get_session() as session:
        return session.query(Baseline).order_by(Baseline.feature_name).all()
