"""
직원 레포지토리 - 제네릭 레포지토리 기반 구현 (Version 2)
"""

from typing import Dict, List, Any, Optional
from app.source.core.domain import Employee
from app.source.core.exceptions import DatabaseError
from app.source.core.logging import get_logger
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.infrastructure.persistence.generic_repository import GenericRepository
from app.source.infrastructure.persistence.schema_definition import SchemaRegistry, create_employee_schema

logger = get_logger(__name__)

class EmployeeRepositoryV2(GenericRepository[Employee]):
    """직원 저장소 - 제네릭 레포지토리 기반"""
    
    def __init__(self, db_connection: DatabaseConnection, logger=None):
        """초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
            logger: 로거 인스턴스 (기본값: None, None인 경우 기본 로거 사용)
        """
        self.logger = logger or get_logger(__name__)
        # 스키마 가져오기 또는 생성
        schema = SchemaRegistry.get("employees") or create_employee_schema()
        super().__init__(db_connection, schema, Employee, self.logger)
        self.logger.debug("EmployeeRepositoryV2 initialized")
    
    def find_by_email(self, email: str) -> Optional[Employee]:
        """이메일로 직원 검색
        
        Args:
            email: 검색할 이메일
            
        Returns:
            직원 객체 또는 None
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"email": email}
            results = self.find_by_criteria(criteria)
            return results[0] if results else None
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding employee by email"
                self.logger.error(error_msg, email=email, error=str(e))
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def find_by_jira_account_id(self, jira_account_id: str) -> Optional[Employee]:
        """Jira account ID로 직원 검색
        
        Args:
            jira_account_id: 검색할 Jira account ID
            
        Returns:
            직원 객체 또는 None
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"jira_account_id": jira_account_id}
            results = self.find_by_criteria(criteria)
            return results[0] if results else None
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding employee by Jira account ID"
                self.logger.error(error_msg, jira_account_id=jira_account_id, error=str(e))
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def find_by_department(self, department: str) -> List[Employee]:
        """부서로 직원 목록 검색
        
        Args:
            department: 검색할 부서
            
        Returns:
            직원 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        criteria = {"department": department}
        return self.find_by_criteria(criteria)
    
    def find_by_position(self, position: str) -> List[Employee]:
        """직급으로 직원 목록 검색
        
        Args:
            position: 검색할 직급
            
        Returns:
            직원 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        criteria = {"position": position}
        return self.find_by_criteria(criteria)
    
    def search(self, keywords: str) -> List[Employee]:
        """키워드로 직원 검색 (이름, 이메일, 부서 등)
        
        Args:
            keywords: 검색 키워드
            
        Returns:
            직원 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            # ILIKE는 PostgreSQL 전용, 대소문자 구분 없이 검색
            query = """
                SELECT * FROM employees 
                WHERE name ILIKE %s 
                OR email ILIKE %s 
                OR department ILIKE %s
                OR position ILIKE %s
            """
            search_pattern = f"%{keywords}%"
            params = (search_pattern, search_pattern, search_pattern, search_pattern)
            
            self.logger.debug("Searching employees", keywords=keywords)
            
            result = self.db.execute_query(query, params)
            
            if not result:
                self.logger.warning("No employees found in search", keywords=keywords)
                return []
            
            employees = [self._map_to_entity(row) for row in result]
            self.logger.debug("Employees found in search", 
                            keywords=keywords, 
                            count=len(employees))
            
            return employees
            
        except Exception as e:
            error_msg = "Database error while searching employees"
            self.logger.error(error_msg, keywords=keywords, error=str(e))
            raise DatabaseError(f"{error_msg}: {str(e)}")
    
    def count(self) -> int:
        """직원 수 조회
        
        Returns:
            직원 수
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.schema.table_name}"
            result = self.db.execute_query(query)
            return result[0]['count'] if result else 0
        except Exception as e:
            error_msg = "Database error while counting employees"
            self.logger.error(error_msg, error=str(e))
            raise DatabaseError(f"{error_msg}: {str(e)}") 