from datetime import date
from typing import Optional

# devcontainer 환경에서 실행할 때 경로 문제 해결 - 상위 디렉토리(source)를 sys.path에 추가
import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection

import psycopg2
import logging

# models/employee.py
class Employee:
    def __init__(self, id, name, email, phone_number, bank_account, position, affiliation = "메테오 시뮬레이션",  signature_path=None,  birth=None):
        self.id = id
        self.name = name
        self.email = email
        self.phone_number = phone_number
        self.signature_path = signature_path
        self.bank_account = bank_account
        self.position = position
        self.affiliation = affiliation
        self.birth = birth

    @staticmethod
    def create_table():
        logging.log(logging.INFO, "Creating employees table...")
        # email을 UNIQUE로 설정
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone_number TEXT,
                bank_account TEXT,
                Affiliation TEXT,
                position TEXT,
                signature_path TEXT,
                birth DATE
            );
        """)
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def insert(name, email, phone_number, bank_account, position, affiliation= "메테오시뮬레이션", signature_path=None, birth=None):
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO employees (name, email, phone_number, bank_account, position, affiliation, signature_path, birth)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id;""",
                (name, email, phone_number, bank_account, position, affiliation, signature_path, birth)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
        except psycopg2.Error as e:
            print("DB insert error:", e)
            conn.rollback()
        finally:
            cur.close()
            conn.close()


    @staticmethod
    def from_row(row):
        """row -> Employee 객체로 변환"""
        return Employee(
            id=row[0],
            name=row[1],
            email=row[2],
            phone_number=row[3],
            bank_account=row[4],
            position=row[5],
            affiliation = row[6],
            signature_path=row[7],
            birth=row[8]
        )

    @staticmethod
    def get_by_id(emp_id: int):
        """ID로 Employee 조회"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, email, phone_number, bank_account, position, affiliation, signature_path, birth FROM employees WHERE id = %s;",
            (emp_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return Employee.from_row(row)
        return None
    
    @staticmethod
    def get_by_email(email: str):
        """이메일로 Employee 조회"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, email, phone_number, bank_account, position, affiliation, signature_path, birth FROM employees WHERE email = %s;",
            (email,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return Employee.from_row(row)
        return None

    @staticmethod
    def get_all():
        """모든 Employee 조회"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, phone_number, bank_account, position, affiliation, signature_path, birth FROM employees ORDER BY id;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [Employee.from_row(r) for r in rows]
    
    @staticmethod
    def delete_table():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS employees;")
        conn.commit()
        cur.close()
        conn.close()



if __name__ == "__main__":
    print(sys.path)
    Employee.delete_table()
    Employee.create_table()
    emp_id = Employee.insert("김자현", "kjh4387@msimul.com", "010-5016-4387", "국민 477002-04-107088", "주임연구원", "메테오 시뮬레이션", "sample_signature_path", date(1996, 2, 15))
    emp_id2 = Employee.insert("황지인", "laplace@msimul.com", "010-1234-5678", "국민 477002-04-107088", "주임연구원", "메테오 시뮬레이션", "sample_signature_path", date(1997, 12, 12))
    print("Inserted employee ID:", emp_id, emp_id2)
    print("kjh4387@msimul.com:", Employee.get_by_email("kjh4387@msimul.com").__dict__)