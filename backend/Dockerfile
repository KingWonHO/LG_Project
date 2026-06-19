FROM python:3.11-slim

# WeasyPrint(PDF) + 한글 폰트
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi-dev libcairo2 fonts-nanum curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data/uploads data/reports data/chroma

EXPOSE 8000
HEALTHCHECK CMD curl --fail http://localhost:8000/api/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
