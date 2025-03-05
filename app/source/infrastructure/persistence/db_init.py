import os
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.core.logging import get_logger

logger = get_logger(__name__)

def init_database(db_connection: DatabaseConnection):
    """데이터베이스 초기화"""
    logger.info("Initializing database tables")
    
    # 회사 테이블 생성
    create_company_table = """
    CREATE TABLE IF NOT EXISTS companies (
        id VARCHAR(50) PRIMARY KEY,
        company_name VARCHAR(100) NOT NULL,
        biz_id VARCHAR(20) NOT NULL,
        rep_name VARCHAR(50),
        address VARCHAR(200),
        biz_type VARCHAR(50),
        biz_item VARCHAR(100),
        phone VARCHAR(20),
        rep_stamp VARCHAR(200)
    );
    """
    
    # 직원 테이블 생성 - VARCHAR 타입으로 수정
    create_employee_table = """
    CREATE TABLE IF NOT EXISTS employees (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        department VARCHAR(50),
        position VARCHAR(50),
        email VARCHAR(100),
        phone VARCHAR(20),
        signature VARCHAR(200)
    );
    """
    
    # 연구 과제 테이블 생성
    create_research_table = """
    CREATE TABLE IF NOT EXISTS research_projects (
        id VARCHAR(50) PRIMARY KEY,
        project_name VARCHAR(100) NOT NULL,
        project_period VARCHAR(100),
        project_manager VARCHAR(50),
        project_code VARCHAR(50)
    );
    """
    
    # 전문가 테이블 생성
    create_expert_table = """
    CREATE TABLE IF NOT EXISTS experts (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        affiliation VARCHAR(100),
        position VARCHAR(50),
        dob VARCHAR(20),
        address VARCHAR(200),
        classification VARCHAR(50),
        email VARCHAR(100),
        phone VARCHAR(20)
    );
    """
    
    # 테이블 생성 실행
    try:
        db_connection.execute_query(create_company_table)
        db_connection.execute_query(create_employee_table)
        db_connection.execute_query(create_research_table)
        db_connection.execute_query(create_expert_table)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise

def cleanup_database(db_connection: DatabaseConnection):
    """테스트 후 데이터베이스 테이블 삭제"""
    logger.info("Cleaning up database tables")
    
    # 테이블 삭제 쿼리
    drop_tables = """
    DROP TABLE IF EXISTS companies CASCADE;
    DROP TABLE IF EXISTS employees CASCADE;
    DROP TABLE IF EXISTS research_projects CASCADE;
    DROP TABLE IF EXISTS experts CASCADE;
    """
    
    try:
        db_connection.execute_query(drop_tables)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise

def check_and_fix_employee_table(db_connection: DatabaseConnection):
    """직원 테이블 스키마 확인 및 수정"""
    logger.info("Checking employee table schema")
    
    # 테이블 존재 여부 확인
    check_query = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'employees'
    );
    """
    
    try:
        result = db_connection.execute_query(check_query)
        table_exists = result[0]['exists']
        
        if table_exists:
            # 컬럼 타입 확인
            column_query = """
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'employees' AND column_name = 'id';
            """
            
            column_result = db_connection.execute_query(column_query)
            
            if column_result and column_result[0]['data_type'] != 'character varying':
                # 테이블 삭제 후 재생성
                logger.warning("Employee table has incorrect schema, recreating...")
                cleanup_database(db_connection)
                init_database(db_connection)
            else:
                logger.info("Employee table schema is correct")
        else:
            # 테이블 생성
            init_database(db_connection)
            
    except Exception as e:
        logger.error("Error checking employee table schema", error=str(e))
        # 오류 발생 시 테이블 재생성
        try:
            cleanup_database(db_connection)
            init_database(db_connection)
        except:
            raise 