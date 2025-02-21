# main-service/app/main.py

from fastapi import FastAPI, Body
import requests
import logger_settings



app = FastAPI()

class template_data:
    def __init__(self, template_name, datas):
        self.template_name = template_name
        self.datas = datas

@app.post("/process-document")
def process_document(data: template_data ):
    """
    전달된 딕셔너리를 바탕으로 템플릿을 사용하여 문서를 생성하고 결과를 반환합니다.
    딕셔너리 내부의 template_name을 바탕으로 템플릿을 찾고, 찾은 템플릿 내부 placeholder를 스캔하여 내부에 들어갈 필드를 파악합니다.
    placeholder 중 DB에 저장된 데이터가 필요한 경우, 해당 데이터를 DB에서 조회하여 딕셔너리에 추가하여 데이터를 완성합니다.
    완성된 데이터를 기반으로 placeholder와 비교하고, 필요한 데이터가 전부 있는 경우 템플릿을 채워서 결과를 반환합니다.

    :param data: template_data 클래스 인스턴스
    """

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


