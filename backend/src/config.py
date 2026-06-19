"""애플리케이션 설정.

.env 파일 또는 환경 변수에서 값을 읽어온다.
사용 예:
    from src.config import settings
    print(settings.llm_model)
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB
    db_url: str = "sqlite:///data/app.db"

    # LLM: Qwen (OpenAI 호환 엔드포인트)
    llm_base_url: str = "http://localhost:8000/v1"
    llm_api_key: str = "not-needed-for-local"
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct"

    # 임베딩 (로컬)
    embedding_model: str = "jhgan/ko-sroberta-multitask"

    # 벡터DB / 데이터 경로
    chroma_dir: str = "data/chroma"
    upload_dir: str = "data/uploads"
    report_dir: str = "data/reports"

    # CORS
    cors_origins: str = "http://localhost:5173"

    # 접근 제어 (ADM-001)
    engineer_access_code: str = "change-me"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
