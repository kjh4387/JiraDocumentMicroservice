import os
import psycopg2

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mydb")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")

def get_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def create_employees_table():
    """employees 테이블을 생성"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                signature_path TEXT
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("employees 테이블 생성(또는 이미 존재).")
    except Exception as e:
        print("테이블 생성 오류:", e)

def insert_employee(name: str, signature: str):
    """employees 테이블에 레코드 삽입"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO employees (name, signature_path) VALUES (%s, %s) RETURNING id;",
            (name, signature)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        print(f"새 사원 id={new_id} inserted.")
    except Exception as e:
        print("데이터 삽입 오류:", e)

def get_all_employees():
    """employees 테이블에서 모든 데이터 조회"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, signature_path FROM employees ORDER BY id;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        employees = []
        for r in rows:
            employees.append({
                "id": r[0],
                "name": r[1],
                "signature_path": r[2]
            })
        return employees
    except Exception as e:
        print("데이터 조회 오류:", e)
        return []

if __name__ == "__main__":
    # 1) 테이블 생성
    create_employees_table()

    # 2) 테스트 데이터 삽입
    insert_employee("Alice", "/app/images/signature_alice.png")
    insert_employee("Bob", "/app/images/signature_bob.png")

    # 3) 조회
    data = get_all_employees()
    print("employees 목록:", data)
