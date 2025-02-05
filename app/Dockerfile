FROM python:3.10-slim

WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 필수 시스템 패키지 설치 (WeasyPrint 등 외부 의존성)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libpq-dev \
    pkg-config \
    libssl-dev \
    ca-certificates\
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 소스 복사
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]