# db.py
import os
import psycopg2
import logging

DB_HOST = os.getenv("DB_HOST", "host.docker.internal") # host.docker.internal은 도커 내부에서 호스트를 가리킴. devcontainer와 app container 모두에서 db container에 접근 가능
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mydb")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")

def get_connection():
    """DB 접속 반환"""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    logging.log(logging.INFO, "DB connection established")
    return conn

if __name__ == "__main__":
    conn = get_connection()
    conn.close()
    logging.log(logging.INFO, "DB connection closed")