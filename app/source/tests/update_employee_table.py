#!/usr/bin/env python3
"""
직원 테이블 스키마 업데이트 스크립트
"""
import psycopg2
import sys

def update_employee_table():
    """직원 테이블 스키마 업데이트"""
    # DB 연결 설정
    db_config = {
        "host": "db",
        "port": 5432,
        "user": "myuser",
        "password": "mypassword",
        "database": "mydb"
    }
    
    conn = None
    
    try:
        print("데이터베이스에 연결 중...")
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 기존 테이블 확인
        print("기존 employees 테이블 구조 확인 중...")
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'employees'
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"기존 컬럼: {existing_columns}")
        
        # 누락된 컬럼 추가
        needed_columns = {
            "stamp": "VARCHAR(255)",
            "bank_name": "VARCHAR(100)",
            "account_number": "VARCHAR(50)"
        }
        
        for column, data_type in needed_columns.items():
            if column.lower() not in [col.lower() for col in existing_columns]:
                print(f"컬럼 추가 중: {column}")
                cursor.execute(f"ALTER TABLE employees ADD COLUMN {column} {data_type}")
                print(f"컬럼 {column} 추가 완료")
            else:
                print(f"컬럼 {column}은 이미 존재합니다")
        
        print("테이블 업데이트 완료")
        return True
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("직원 테이블 업데이트 시작...")
    success = update_employee_table()
    sys.exit(0 if success else 1)