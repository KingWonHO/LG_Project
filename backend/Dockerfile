FROM python:3.11-slim

# WeasyPrint(PDF) 라이브러리 + 한글 폰트(fonts-nanum) + curl(헬스체크)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi-dev libcairo2 fonts-nanum curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# RAG 임베딩 모델을 이미지에 미리 내려받아 런타임에 오프라인 동작하게 함.
# (빌드 시 인터넷 필요 · 사내망 프록시면 HF_ENDPOINT/HTTPS_PROXY build-arg로 조정)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('jhgan/ko-sroberta-multitask')"

COPY . .
RUN mkdir -p data/uploads data/reports data/chroma

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=5 \
    CMD curl --fail http://localhost:8000/api/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
