"""애플리케이션 설정.

.env 파일 또는 환경 변수에서 값을 읽어옵니다.
사용 예:
    from src.config import settings
    print(settings.db_url)
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB
    db_url: str = "sqlite:///data/app.db"

    # 로컬 LLM
    ollama_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1:8b"

    # 로컬 임베딩
    embedding_model: str = "jhgan/ko-sroberta-multitask"

    # 벡터 DB / 데이터 경로
    chroma_dir: str = "data/chroma"
    upload_dir: str = "data/uploads"
    report_dir: str = "data/reports"

    # 접근 제어 (ADM-001)
    engineer_access_code: str = "change-me"


settings = Settings()
