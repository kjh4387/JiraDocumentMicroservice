"""
회사 레포지토리 - 제네릭 레포지토리 기반 구현 (Version 2)
"""

from typing import Dict, List, Any, Optional
from app.source.core.domain import Company
from app.source.core.exceptions import DatabaseError
from app.source.core.logging import get_logger
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.infrastructure.persistence.generic_repository import GenericRepository
from app.source.infrastructure.persistence.schema_definition import SchemaRegistry, create_company_schema

logger = get_logger(__name__)

class CompanyRepositoryV2(GenericRepository[Company]):
    """회사 저장소 - 제네릭 레포지토리 기반"""
    
    def __init__(self, db_connection: DatabaseConnection, logger=None):
        """초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
            logger: 로거 인스턴스 (기본값: None, None인 경우 기본 로거 사용)
        """
        self.logger = logger or get_logger(__name__)
        # 스키마 가져오기 또는 생성
        schema = SchemaRegistry.get("companies") or create_company_schema()
        super().__init__(db_connection, schema, Company, self.logger)
        self.logger.debug("CompanyRepositoryV2 initialized")
    
    def find_by_name(self, company_name: str) -> Optional[Company]:
        """회사명으로 회사 검색
        
        Args:
            company_name: 검색할 회사명
            
        Returns:
            회사 객체 또는 None
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"company_name": company_name}
            results = self.find_by_criteria(criteria)
            return results[0] if results else None
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding company by name"
                self.logger.error(error_msg, company_name=company_name, error=str(e))
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def search(self, keywords: str) -> List[Company]:
        """키워드로 회사 검색 (회사명)
        
        Args:
            keywords: 검색 키워드
            
        Returns:
            회사 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            # ILIKE는 PostgreSQL 전용, 대소문자 구분 없이 검색
            query = """
                SELECT * FROM companies 
                WHERE company_name ILIKE %s 
                OR address ILIKE %s
            """
            search_pattern = f"%{keywords}%"
            params = (search_pattern, search_pattern)
            
            self.logger.debug("Searching companies", keywords=keywords)
            
            result = self.db.execute_query(query, params)
            
            if not result:
                self.logger.warning("No companies found in search", keywords=keywords)
                return []
            
            companies = [self._map_to_entity(row) for row in result]
            self.logger.debug("Companies found in search", 
                            keywords=keywords, 
                            count=len(companies))
            
            return companies
            
        except Exception as e:
            error_msg = "Database error while searching companies"
            self.logger.error(error_msg, keywords=keywords, error=str(e))
            raise DatabaseError(f"{error_msg}: {str(e)}")
    
    def count(self) -> int:
        """회사 수 조회
        
        Returns:
            회사 수
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.schema.table_name}"
            result = self.db.execute_query(query)
            return result[0]['count'] if result else 0
        except Exception as e:
            error_msg = "Database error while counting companies"
            self.logger.error(error_msg, error=str(e))
            raise DatabaseError(f"{error_msg}: {str(e)}") 