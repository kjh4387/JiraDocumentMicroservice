FROM python:3.10-slim


WORKDIR /app

#의존성 복사 및 설치
COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    pkg-config \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

#소스 파일 복사
COPY source/ .

EXPOSE 8001

CMD ["uvicorn", "app.gen:app", "--host", "0.0.0.0", "--port", "8001"]