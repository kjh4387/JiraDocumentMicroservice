"""
연구과제 레포지토리 - 제네릭 레포지토리 기반 구현 (Version 2)
"""

from typing import Dict, List, Any, Optional
from app.source.core.domain import Research
from app.source.core.exceptions import DatabaseError
from app.source.core.logging import get_logger
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.infrastructure.persistence.generic_repository import GenericRepository
from app.source.infrastructure.persistence.schema_definition import SchemaRegistry, create_research_schema

logger = get_logger(__name__)

class ResearchRepositoryV2(GenericRepository[Research]):
    """연구과제 저장소 - 제네릭 레포지토리 기반"""
    
    def __init__(self, db_connection: DatabaseConnection, logger=None):
        """초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
            logger: 로거 인스턴스 (기본값: None, None인 경우 기본 로거 사용)
        """
        self.logger = logger or get_logger(__name__)
        # 스키마 가져오기 또는 생성
        schema = SchemaRegistry.get("research_projects") or create_research_schema()
        super().__init__(db_connection, schema, Research, self.logger)
        self.logger.debug("ResearchRepositoryV2 initialized")
    
    def find_by_title(self, title: str) -> Optional[Research]:
        """제목으로 연구과제 검색
        
        Args:
            title: 검색할 연구과제 제목
            
        Returns:
            연구과제 객체 또는 None
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"title": title}
            results = self.find_by_criteria(criteria)
            return results[0] if results else None
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding research by title"
                self.logger.error(error_msg, title=title, error=str(e))
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def find_by_company_id(self, company_id: str) -> List[Research]:
        """회사 ID로 연구과제 목록 검색
        
        Args:
            company_id: 검색할 회사 ID
            
        Returns:
            연구과제 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        criteria = {"company_id": company_id}
        return self.find_by_criteria(criteria)
    
    def find_by_status(self, status: str) -> List[Research]:
        """상태로 연구과제 목록 검색
        
        Args:
            status: 검색할 상태
            
        Returns:
            연구과제 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        criteria = {"status": status}
        return self.find_by_criteria(criteria)
    
    def search(self, keywords: str) -> List[Research]:
        """키워드로 연구과제 검색 (제목, 내용)
        
        Args:
            keywords: 검색 키워드
            
        Returns:
            연구과제 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            # ILIKE는 PostgreSQL 전용, 대소문자 구분 없이 검색
            query = """
                SELECT * FROM research_projects 
                WHERE title ILIKE %s 
                OR description ILIKE %s
                OR researcher_name ILIKE %s
            """
            search_pattern = f"%{keywords}%"
            params = (search_pattern, search_pattern, search_pattern)
            
            self.logger.debug("Searching research projects", keywords=keywords)
            
            result = self.db.execute_query(query, params)
            
            if not result:
                self.logger.warning("No research projects found in search", keywords=keywords)
                return []
            
            research_projects = [self._map_to_entity(row) for row in result]
            self.logger.debug("Research projects found in search", 
                            keywords=keywords, 
                            count=len(research_projects))
            
            return research_projects
            
        except Exception as e:
            error_msg = "Database error while searching research projects"
            self.logger.error(error_msg, keywords=keywords, error=str(e))
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
            self.logger.error(error_msg, error=str(e))
            raise DatabaseError(f"{error_msg}: {str(e)}") 