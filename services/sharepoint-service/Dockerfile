FROM python:3.10-slim

WORKDIR /app

#의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y ca-certificates

#소스 복사
COPY source/ .

EXPOSE 8002

CMD ["uvicorn", "post:app", "--host", "0.0.0.0", "--port", "8002"]