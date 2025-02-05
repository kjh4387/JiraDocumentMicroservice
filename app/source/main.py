# main-service/app/main.py

from fastapi import FastAPI, Body
import requests

app = FastAPI()

@app.post("/process-document")
def process_document(data: dict = Body(...)):
    """
    1) doc-gen-service에 문서 생성 요청
    2) 생성된 문서를 post-service로 전송 요청
    3) 최종 결과를 반환
    """
    doc_gen_url = "http://doc-gen-service:8001/generate-pdf"
    post_url = "http://post-service:8002/post-document"

    # 1) 문서 생성 요청
    gen_resp = requests.post(doc_gen_url, json=data)
    if gen_resp.status_code != 200:
        return {"error": "Failed to generate document"}

    # doc-gen-service로부터 생성된 PDF 경로를 받았다고 가정
    pdf_info = gen_resp.json()  # e.g., {"pdf_path": "/app/generated/example.pdf"}

    # 2) post-service에 업로드 요청
    post_resp = requests.post(post_url, json=pdf_info)
    if post_resp.status_code != 200:
        return {"error": "Failed to post document to external system"}

    return {
        "message": "Document processed successfully",
        "doc_gen_result": pdf_info,
        "post_result": post_resp.json()
    }

@app.get("/")
def read_root():
    return {"message": "Main service is running"}


import os
import psycopg2
from fastapi import FastAPI

app = FastAPI()

# 환경 변수에서 DB 접속 정보 가져오기
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mydb")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")

@app.on_event("startup")
def startup_event():
    """ 애플리케이션 시작 시 DB 초기화/테스트 쿼리 예시 """
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        # 예시로 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT
            );
        """)
        conn.commit()
        cursor.close()
        print("DB connected and table created/verified.")
    except Exception as e:
        print("DB connection failed:", e)
    finally:
        if conn:
            conn.close()

@app.get("/")
def read_root():
    return {"message": "Hello, DB setup success!"}

@app.post("/add-customer")
def add_customer(name: str, email: str = None):
    """ 예시: 고객 정보를 DB에 추가 """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO customers (name, email) VALUES (%s, %s) RETURNING id;",
                       (name, email))
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Customer added", "id": new_id}
    except Exception as e:
        return {"error": str(e)}

@app.get("/customers")

def get_customers():
    """ 예시: 모든 고객 목록 조회 """
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email FROM customers;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        # rows -> [{"id":1, "name":"...", "email":"..."}] 형태 변환
        customers = [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]
        return {"customers": customers}
    except Exception as e:
        return {"error": str(e)}
