#!/usr/bin/env python3
"""
테이블 재생성 스크립트
"""
import psycopg2
import sys

def recreate_tables():
    """테이블 재생성"""
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
        
        # 테이블 드롭 및 생성
        print("research_projects 테이블 재생성 중...")
        cursor.execute("DROP TABLE IF EXISTS research_projects")
        cursor.execute("""
        CREATE TABLE research_projects (
            id VARCHAR(50) PRIMARY KEY,
            project_name VARCHAR(100) NOT NULL,
            project_code VARCHAR(50) NOT NULL UNIQUE,
            project_period VARCHAR(100),
            project_manager VARCHAR(100),
            project_manager_phone VARCHAR(30)
        )
        """)
        
        # 기존 테이블 처리
        print("기존 researches 테이블 확인 중...")
        cursor.execute("DROP TABLE IF EXISTS researches")
        
        print("테이블 재생성 완료")
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
    print("테이블 재생성 시작...")
    success = recreate_tables()
    sys.exit(0 if success else 1) 