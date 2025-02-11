# models/research.py
from datetime import date
from typing import Optional

# devcontainer 환경에서 실행할 때 경로 문제 해결 - 상위 디렉토리(source)를 sys.path에 추가
import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection

import psycopg2
import logging

class Research:
    def __init__(self, id, research_name,research_key, manager, start_date:date, end_date:date, budget, status, description):
        self.id = id
        self.research_name = research_name
        self.research_key = research_key
        self.manager = manager
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget
        self.status = status
        self.description = description

    @staticmethod
    def create_table():
        logging.log(logging.INFO, "Creating research table...")
        # email을 UNIQUE로 설정
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS research (
                id SERIAL PRIMARY KEY,
                research_name TEXT NOT NULL,
                research_key TEXT unique,
                manager TEXT NOT NULL,
                start_date DATE,
                end_date DATE,
                budget INT,
                status TEXT,
                description TEXT
            );
        """)
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def insert(research_name, research_key, manager, start_date, end_date, budget = 0, status = "in_progress", description = ""):
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO research (research_name, research_key, manager, start_date, end_date, budget, status, description)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id;""",
                (research_name, research_key, manager, start_date, end_date, budget, status, description)
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
        return Research(
            id=row[0],
            research_name=row[1],
            research_key=row[2],
            manager=row[3],
            start_date=row[4],
            end_date=row[5],
            budget= row[6] if row[6] is not None else None,
            status=row[7] if row[7] is not None else "in progress",
            description=row[8] if row[8] is not None else None
            
        )

    @staticmethod
    def get_by_id(emp_id: int):
        """ID로 Research 조회"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, research_name, manager, start_date, end_date, budget, status, description FROM research WHERE id = %s;",
            (emp_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return Research.from_row(row)
        return None
    
    @staticmethod
    def get_by_key(research_key: str):
        """과제번호로 연구과제 조회"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, research_name, research_key, manager, start_date, end_date, budget, status, description FROM research WHERE research_key = %s;",
            (research_key,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return Research.from_row(row)
        return None

    @staticmethod
    def get_all():
        """모든 Employee 조회"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, research_name, research_key, manager, start_date, end_date, budget, status, description FROM research ORDER BY id;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [Research.from_row(r) for r in rows]
    
    @staticmethod
    def delete_table():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS research;")
        conn.commit()
        cur.close()
        conn.close()



if __name__ == "__main__":
    print(sys.path)
    Research.delete_table()
    Research.create_table()
    res_id = Research.insert("배터리/ESS/전기자동차 화재 확산과 피해 예측을 위한 인공지능 응용형 시뮬레이션 프로그램 개발", "RS-2023-00217016", "김지태", "2023-04-01","2027-03-31")
    print("Inserted Research ID:", res_id)
    print("RS-2023-00217016:", Research.get_by_key("RS-2023-00217016").__dict__)