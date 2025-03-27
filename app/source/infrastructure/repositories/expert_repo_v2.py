"""
전문가 레포지토리 - 제네릭 레포지토리 기반 구현 (Version 2)
"""

from typing import Dict, List, Any, Optional
from app.source.core.domain import Expert
from app.source.core.exceptions import DatabaseError
import logging
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.infrastructure.persistence.generic_repository import GenericRepository
from app.source.infrastructure.persistence.schema_definition import SchemaRegistry, create_expert_schema

logger = logging.getLogger(__name__)

class ExpertRepositoryV2(GenericRepository[Expert]):
    """전문가 저장소 - 제네릭 레포지토리 기반"""
    
    def __init__(self, db_connection: DatabaseConnection, logger=None):
        """초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
            logger: 로거 인스턴스 (기본값: None, None인 경우 기본 로거 사용)
        """
        self.logger = logger or logging.getLogger(__name__)
        # 스키마 가져오기 또는 생성
        schema = SchemaRegistry.get("experts") or create_expert_schema()
        super().__init__(db_connection, schema, Expert, self.logger)
        self.logger.debug("ExpertRepositoryV2 initialized")
    
    def find_by_id(self, expert_id: str) -> Optional[Expert]:
        """ID로 전문가 검색
        
        Args:
            expert_id: 검색할 전문가 ID
            
        Returns:
            전문가 객체 또는 None
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"id": expert_id}
            results = self.find_by_criteria(criteria)
            return results[0] if results else None
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding expert by ID"
                self.logger.error("%s: %s (expert_id=%s)", error_msg, str(e), expert_id)
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def find_by_specialty(self, specialty: str) -> List[Expert]:
        """전문 분야로 전문가 목록 검색
        
        Args:
            specialty: 검색할 전문 분야
            
        Returns:
            전문가 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"specialty": specialty}
            return self.find_by_criteria(criteria)
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding experts by specialty"
                self.logger.error("%s: %s (specialty=%s)", error_msg, str(e), specialty)
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def find_by_expertise(self, expertise: str) -> List[Expert]:
        """전문 분야로 전문가 목록 검색
        
        Args:
            expertise: 검색할 전문 분야
            
        Returns:
            전문가 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            criteria = {"expertise": expertise}
            return self.find_by_criteria(criteria)
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while finding experts by expertise"
                self.logger.error("%s: %s (expertise=%s)", error_msg, str(e), expertise)
                raise DatabaseError(f"{error_msg}: {str(e)}")
            raise e
    
    def search(self, keywords: str) -> List[Expert]:
        """키워드로 전문가 검색 (이름, 전문분야, 소속)
        
        Args:
            keywords: 검색 키워드
            
        Returns:
            전문가 객체 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            query = """
                SELECT * FROM experts 
                WHERE name ILIKE %s 
                OR expertise ILIKE %s
                OR organization ILIKE %s
            """
            search_pattern = f"%{keywords}%"
            params = (search_pattern, search_pattern, search_pattern)
            
            self.logger.debug("Searching experts with keywords: %s", keywords)
            
            result = self.db.execute_query(query, params)
            
            if not result:
                self.logger.warning("No experts found in search with keywords: %s", keywords)
                return []
            
            experts = [self._map_to_entity(row) for row in result]
            self.logger.debug("Experts found in search: %d (keywords=%s)", len(experts), keywords)
            
            return experts
            
        except Exception as e:
            error_msg = "Database error while searching experts"
            self.logger.error("%s: %s (keywords=%s)", error_msg, str(e), keywords)
            raise DatabaseError(f"{error_msg}: {str(e)}")
    
    def count(self) -> int:
        """전문가 수 조회
        
        Returns:
            전문가 수
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.schema.table_name}"
            result = self.db.execute_query(query)
            return result[0]['count'] if result else 0
        except Exception as e:
            error_msg = "Database error while counting experts"
            self.logger.error("%s: %s", error_msg, str(e))
            raise DatabaseError(f"{error_msg}: {str(e)}") 