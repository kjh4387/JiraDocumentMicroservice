FROM python:3.10-slim

WORKDIR /app

# 필수 시스템 패키지 설치 (WeasyPrint 등 외부 의존성)
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
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# source 폴더 내의 모든 파일을 /app 으로 복사
COPY source/ .

# 포트 노출
EXPOSE 8001

# 애플리케이션 실행
# 만약 gen.py 파일 내에 FastAPI 인스턴스가 app 이름으로 정의되어 있다면 아래와 같이 실행합니다.
CMD ["uvicorn", "gen:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
