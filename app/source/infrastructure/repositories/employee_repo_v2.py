"""
직원 레포지토리 - 제네릭 레포지토리 기반 구현 (Version 2)
"""

from typing import Dict, List, Any, Optional
from app.source.core.domain import Employee
from app.source.core.exceptions import DatabaseError
import logging
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.infrastructure.persistence.generic_repository import GenericRepository
from app.source.infrastructure.persistence.schema_definition import SchemaRegistry, create_employee_schema

logger = logging.getLogger(__name__)

class EmployeeRepositoryV2(GenericRepository[Employee]):
    """직원 저장소 - 제네릭 레포지토리 기반"""
    
    def __init__(self, db_connection: DatabaseConnection, logger=None):
        """초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
            logger: 로거 인스턴스 (기본값: None, None인 경우 기본 로거 사용)
        """
        self.logger = logger or logging.getLogger(__name__)
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
                self.logger.error("%s: %s (email=%s)", error_msg, str(e), email)
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def find_by_jira_account_id(self, account_id: str) -> Optional[Employee]:
        """Jira 계정 ID로 직원 검색
        
        Args:
            account_id: 검색할 Jira 계정 ID
            
        Returns:
            직원 객체 또는 None
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"jira_account_id": account_id}
            results = self.find_by_criteria(criteria)
            return results[0] if results else None
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding employee by account ID"
                self.logger.error("%s: %s (account_id=%s)", error_msg, str(e), account_id)
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
        """키워드로 직원 검색 (이름, 이메일, 부서)
        
        Args:
            keywords: 검색 키워드
            
        Returns:
            직원 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            query = """
                SELECT * FROM employees 
                WHERE name ILIKE %s 
                OR email ILIKE %s
                OR department ILIKE %s
            """
            search_pattern = f"%{keywords}%"
            params = (search_pattern, search_pattern, search_pattern)
            
            self.logger.debug("Searching employees with keywords: %s", keywords)
            
            result = self.db.execute_query(query, params)
            
            if not result:
                self.logger.warning("No employees found in search with keywords: %s", keywords)
                return []
            
            employees = [self._map_to_entity(row) for row in result]
            self.logger.debug("Employees found in search: %d (keywords=%s)", len(employees), keywords)
            
            return employees
            
        except Exception as e:
            error_msg = "Database error while searching employees"
            self.logger.error("%s: %s (keywords=%s)", error_msg, str(e), keywords)
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
            self.logger.error("%s: %s", error_msg, str(e))
            raise DatabaseError(f"{error_msg}: {str(e)}") 