from typing import Dict, Any, List, Optional
from datetime import date
import uuid
import psycopg2
import psycopg2.extras
from app.source.core.domain import Company, Employee, Research, Expert
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.config.di_container import DIContainer

def get_test_config():
    """테스트용 설정 반환"""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "user": "test_user",
            "password": "test_password",
            "database": "test_db"
        },
        "schema_path": "app/source/schemas/IntegratedDocumentSchema.json",
        "template_dir": "app/source/templates"
    }

class TestFixtures:
    """테스트에 사용할 공통 데이터 및 객체"""
    
    @staticmethod
    def create_test_company(override_data: Dict[str, Any] = None) -> Company:
        """테스트용 회사 객체 생성"""
        company_id = f"TEST-COMP-{uuid.uuid4().hex[:8]}"
        data = {
            "id": company_id,
            "company_name": "테스트 회사",
            "biz_id": "123-45-67890",
            "email": "test@company.com",
            "rep_name": "대표자",
            "address": "서울시 강남구 테스트로 123",
            "biz_type": "서비스업",
            "biz_item": "소프트웨어 개발",
            "phone": "02-1234-5678",
            "fax": "02-1234-5679"
        }
        
        if override_data:
            data.update(override_data)
            
        return Company(**data)
    
    @staticmethod
    def create_test_employee(override_data: Dict[str, Any] = None) -> Employee:
        """테스트용 직원 객체 생성"""
        employee_id = f"TEST-EMP-{uuid.uuid4().hex[:8]}"
        data = {
            "id": employee_id,
            "name": "홍길동",
            "email": "test@example.com",
            "department": "개발팀",
            "position": "선임연구원",
            "phone": "010-1234-5678",
            "signature": None,
            "stamp": None,
            "bank_name": "테스트은행",
            "account_number": "123-456-789",
            "birth_date": date(1990, 1, 1),
            "address": "서울시 강남구 테스트로 123",
            "jira_account_id": f"712020:{uuid.uuid4()}"
        }
        
        if override_data:
            data.update(override_data)
            
        return Employee(**data)
    
    @staticmethod
    def create_test_research(override_data: Dict[str, Any] = None) -> Research:
        """테스트용 연구 과제 객체 생성"""
        research_id = f"TEST-RES-{uuid.uuid4().hex[:8]}"
        data = {
            "id": research_id,
            "project_name": "테스트 연구 과제",
            "project_code": "R-2023-001",
            "project_period": "2023-01-01 ~ 2023-12-31",
            "project_manager": "홍길동",
            "project_start_date": date(2023, 1, 1),
            "project_end_date": date(2023, 12, 31),
            "budget": 100000000,
            "status": "진행중",
            "description": "테스트 연구 과제 설명"
        }
        
        if override_data:
            data.update(override_data)
            
        return Research(**data)
    
    @staticmethod
    def create_test_expert(override_data: Dict[str, Any] = None) -> Expert:
        """테스트용 전문가 객체 생성"""
        expert_id = f"TEST-EXP-{uuid.uuid4().hex[:8]}"
        data = {
            "id": expert_id,
            "name": "김전문",
            "affiliation": "테스트대학교",
            "position": "교수",
            "birth_date": date(1980, 1, 1),
            "address": "서울시 관악구 테스트로 456",
            "classification": "학계",
            "email": "expert@test.ac.kr",
            "phone": "010-9876-5432",
            "bank_name": "테스트은행",
            "account_number": "987-654-321",
            "specialty": "인공지능",
            "bio": "인공지능 분야 전문가"
        }
        
        if override_data:
            data.update(override_data)
            
        return Expert(**data)

class MockDatabaseConnection:
    """테스트용 데이터베이스 연결 모의 객체"""
    
    def __init__(self):
        self.executed_queries = []
        self.query_results = {}
        self.default_results = []
    
    def set_result_for_query(self, query: str, result):
        """특정 쿼리에 대한 결과 설정"""
        self.query_results[query] = result
    
    def set_default_result(self, result):
        """기본 결과 설정"""
        self.default_results = result
    
    def execute_query(self, query: str, params=None):
        """쿼리 실행 기록 및 미리 설정된 결과 반환"""
        self.executed_queries.append({"query": query, "params": params})
        
        # 정확한 쿼리 매칭
        if query in self.query_results:
            return self.query_results[query]
        
        # SELECT 쿼리 확인
        if query.strip().upper().startswith("SELECT"):
            return self.default_results
            
        # INSERT, UPDATE, DELETE는 빈 리스트 반환
        return []

class TestDatabaseHelper:
    """테스트 데이터베이스 헬퍼"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config["database"]
    
    def setup_test_db(self):
        """테스트 데이터베이스 설정"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 테스트 테이블 생성
        self._create_test_tables(cursor)
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def cleanup_test_db(self):
        """테스트 데이터 정리"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 테스트 데이터만 삭제 (ID가 TEST로 시작하는 데이터)
        tables = ["employees", "companies", "research_projects", "experts"]
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE id LIKE 'TEST-%'")
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def _get_connection(self):
        """데이터베이스 연결 반환"""
        return psycopg2.connect(
            host=self.config["host"],
            port=self.config["port"],
            user=self.config["user"],
            password=self.config["password"],
            database=self.config["database"]
        )
    
    def _create_test_tables(self, cursor):
        """테스트 테이블 생성"""
        # 회사 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id VARCHAR(50) PRIMARY KEY,
                company_name VARCHAR(100) NOT NULL,
                biz_id VARCHAR(20) NOT NULL,
                rep_name VARCHAR(50),
                address VARCHAR(200),
                biz_type VARCHAR(50),
                biz_item VARCHAR(100),
                phone VARCHAR(20),
                fax VARCHAR(20),
                email VARCHAR(100),
                rep_stamp TEXT
            )
        """)
        
        # 직원 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                department VARCHAR(50),
                position VARCHAR(50),
                phone VARCHAR(20),
                signature TEXT,
                stamp TEXT,
                bank_name VARCHAR(50),
                account_number VARCHAR(50),
                birth_date DATE,
                address VARCHAR(200),
                fax VARCHAR(20)
            )
        """)
        
        # 연구 과제 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_projects (
                id VARCHAR(50) PRIMARY KEY,
                project_name VARCHAR(100) NOT NULL,
                project_code VARCHAR(50) NOT NULL,
                project_period VARCHAR(100),
                project_manager VARCHAR(50),
                project_start_date DATE,
                project_end_date DATE,
                budget BIGINT,
                status VARCHAR(20),
                description TEXT
            )
        """)
        
        # 전문가 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experts (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                affiliation VARCHAR(100),
                position VARCHAR(50),
                birth_date DATE,
                address VARCHAR(200),
                classification VARCHAR(50),
                email VARCHAR(100),
                phone VARCHAR(20),
                bank_name VARCHAR(50),
                account_number VARCHAR(50),
                specialty VARCHAR(100),
                bio TEXT
            )
        """) 