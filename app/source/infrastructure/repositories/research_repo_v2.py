"""
연구 과제 레포지토리 - 제네릭 레포지토리 기반 구현 (Version 2)
"""

from typing import Dict, List, Any, Optional
from app.source.core.domain import Research
from app.source.core.exceptions import DatabaseError
import logging
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.infrastructure.persistence.generic_repository import GenericRepository
from app.source.infrastructure.persistence.schema_definition import SchemaRegistry, create_research_schema

logger = logging.getLogger(__name__)

class ResearchRepositoryV2(GenericRepository[Research]):
    """연구 과제 저장소 - 제네릭 레포지토리 기반"""
    
    def __init__(self, db_connection: DatabaseConnection, logger=None):
        """초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
            logger: 로거 인스턴스 (기본값: None, None인 경우 기본 로거 사용)
        """
        self.logger = logger or logging.getLogger(__name__)
        # 스키마 가져오기 또는 생성
        schema = SchemaRegistry.get("research_projects") or create_research_schema()
        super().__init__(db_connection, schema, Research, self.logger)
        self.logger.debug("ResearchRepositoryV2 initialized")
    
    def find_by_project_code(self, project_code: str) -> Optional[Research]:
        """프로젝트 코드로 연구 과제 검색
        
        Args:
            project_code: 검색할 프로젝트 코드
            
        Returns:
            연구 과제 객체 또는 None
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"project_code": project_code}
            results = self.find_by_criteria(criteria)
            return results[0] if results else None
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding research by project code"
                self.logger.error("%s: %s (project_code=%s)", error_msg, str(e), project_code)
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def find_by_project_manager(self, project_manager: str) -> List[Research]:
        """프로젝트 관리자로 연구 과제 목록 검색
        
        Args:
            project_manager: 검색할 프로젝트 관리자
            
        Returns:
            연구 과제 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"project_manager": project_manager}
            return self.find_by_criteria(criteria)
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding research by project manager"
                self.logger.error("%s: %s (project_manager=%s)", error_msg, str(e), project_manager)
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def find_by_code(self, code: str) -> Optional[Research]:
        """코드로 연구 과제 검색
        
        Args:
            code: 검색할 코드

        Returns:
            연구 과제 객체 또는 None
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"project_code": code}
            results = self.find_by_criteria(criteria)
            return results[0] if results else None
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding research by code"
                self.logger.error("%s: %s (code=%s)", error_msg, str(e), code)
                raise DatabaseError(f"{error_msg}: {str(e)}")
    
    def find_by_status(self, status: str) -> List[Research]:
        """상태로 연구 과제 목록 검색
        
        Args:
            status: 검색할 상태
            
        Returns:
            연구 과제 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"status": status}
            return self.find_by_criteria(criteria)
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding research by status"
                self.logger.error("%s: %s (status=%s)", error_msg, str(e), status)
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def search(self, keywords: str) -> List[Research]:
        """키워드로 연구 과제 검색 (프로젝트명, 프로젝트 코드, 설명)
        
        Args:
            keywords: 검색 키워드
            
        Returns:
            연구 과제 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            query = """
                SELECT * FROM research_projects 
                WHERE project_name ILIKE %s 
                OR project_code ILIKE %s
                OR description ILIKE %s
            """
            search_pattern = f"%{keywords}%"
            params = (search_pattern, search_pattern, search_pattern)
            
            self.logger.debug("Searching research projects with keywords: %s", keywords)
            
            result = self.db.execute_query(query, params)
            
            if not result:
                self.logger.warning("No research projects found in search with keywords: %s", keywords)
                return []
            
            projects = [self._map_to_entity(row) for row in result]
            self.logger.debug("Research projects found in search: %d (keywords=%s)", len(projects), keywords)
            
            return projects
            
        except Exception as e:
            error_msg = "Database error while searching research projects"
            self.logger.error("%s: %s (keywords=%s)", error_msg, str(e), keywords)
            raise DatabaseError(f"{error_msg}: {str(e)}")
    
    def count(self) -> int:
        """연구과제 수 조회
        
        Returns:
            연구과제 수
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.schema.table_name}"
            result = self.db.execute_query(query)
            return result[0]['count'] if result else 0
        except Exception as e:
            error_msg = "Database error while counting research projects"
            self.logger.error("%s: %s", error_msg, str(e))
            raise DatabaseError(f"{error_msg}: {str(e)}") 