"""
제네릭 레포지토리 모듈

스키마 정의를 기반으로 DB 작업을 수행하는 공통 레포지토리 구현
"""

from typing import Dict, List, Any, Optional, Type, TypeVar, Generic, Tuple
from app.source.core.exceptions import DatabaseError
from app.source.core.logging import get_logger
from app.source.infrastructure.persistence.schema_definition import TableSchema, SchemaRegistry
from app.source.infrastructure.persistence.db_connection import DatabaseConnection

logger = get_logger(__name__)

# 제네릭 타입 정의
T = TypeVar('T')

class GenericRepository(Generic[T]):
    """제네릭 레포지토리 - 스키마 기반 DB 작업 수행"""
    
    def __init__(self, db_connection: DatabaseConnection, schema: TableSchema, 
                 entity_class: Type[T], logger=None):
        """초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
            schema: 테이블 스키마
            entity_class: 엔티티 클래스
            logger: 로거 인스턴스 (기본값: None, None인 경우 기본 로거 사용)
        """
        self.db = db_connection
        self.schema = schema
        self.entity_class = entity_class
        self.logger = logger or get_logger(__name__)
        self.logger.debug(f"GenericRepository initialized for {schema.table_name}")
    
    def find_by_id(self, id_value: str) -> Optional[T]:
        """ID로 엔티티 조회
        
        Args:
            id_value: 조회할 엔티티 ID
            
        Returns:
            조회된 엔티티 또는 None
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            query = self.schema.select_by_id_sql()
            params = (id_value,)
            
            self.logger.debug(f"Finding entity by ID", 
                         table=self.schema.table_name, 
                         id=id_value, 
                         query=query)
            
            result = self.db.execute_query(query, params)
            
            if not result:
                self.logger.warning(f"Entity not found", 
                               table=self.schema.table_name, 
                               id=id_value)
                return None
            
            entity = self._map_to_entity(result[0])
            self.logger.debug(f"Entity found", 
                         table=self.schema.table_name, 
                         id=id_value)
            
            return entity
            
        except Exception as e:
            error_msg = f"Database error while finding entity by ID"
            self.logger.error(error_msg, 
                         table=self.schema.table_name, 
                         id=id_value, 
                         error=str(e))
            raise DatabaseError(f"{error_msg} in {self.schema.table_name}: {str(e)}")
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """조건으로 엔티티 조회
        
        Args:
            criteria: 조회 조건 (컬럼명: 값)
            
        Returns:
            조회된 엔티티 목록
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            # 원래 코드로 복구
            query, params = self.schema.select_by_criteria_sql(criteria)
            
            self.logger.debug(f"Finding entities by criteria", 
                         table=self.schema.table_name, 
                         criteria=criteria, 
                         query=query)
            
            result = self.db.execute_query(query, params)
            
            if not result:
                self.logger.warning(f"Entities not found", 
                               table=self.schema.table_name, 
                               criteria=criteria)
                return []
            
            entities = [self._map_to_entity(row) for row in result]
            self.logger.debug(f"Entities found", 
                         table=self.schema.table_name, 
                         count=len(entities))
            
            return entities
            
        except Exception as e:
            error_msg = f"Database error while finding entities by criteria"
            self.logger.error(error_msg, 
                         table=self.schema.table_name, 
                         criteria=criteria, 
                         error=str(e))
            raise DatabaseError(f"{error_msg} in {self.schema.table_name}: {str(e)}")
    
    def exists_by_id(self, id_value: str) -> bool:
        """ID로 엔티티 존재 여부 확인
        
        Args:
            id_value: 엔티티 ID
            
        Returns:
            존재 여부
            
        Raises:
            DatabaseError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            primary_key = self.schema.primary_key
            if not primary_key:
                raise ValueError(f"Primary key not found in {self.schema.table_name}")
                
            query = f"SELECT 1 FROM {self.schema.table_name} WHERE {primary_key.name} = %s LIMIT 1"
            
            result = self.db.execute_query(query, (id_value,))
            
            # 결과가 None이 아니고 비어 있지 않으면 존재
            return result is not None and len(result) > 0
            
        except Exception as e:
            if not isinstance(e, DatabaseError):
                error_msg = "Database error while checking entity existence"
                self.logger.error(error_msg, 
                               table=self.schema.table_name, 
                               id=id_value, 
                               error=str(e))
                raise DatabaseError(f"{error_msg} in {self.schema.table_name}: {str(e)}")
            raise e
    
    def save(self, entity: T) -> T:
        """엔티티 저장 (INSERT 또는 UPDATE)
        
        Args:
            entity: 저장할 엔티티
            
        Returns:
            저장된 엔티티
            
        Raises:
            DatabaseError: 데이터베이스 저장 중 오류 발생 시
        """
        try:
            id_value = getattr(entity, self.schema.primary_key.name)
            exists = self.exists_by_id(id_value) if id_value else False
            
            if exists:
                return self._update(entity)
            else:
                return self._insert(entity)
                
        except Exception as e:
            if not isinstance(e, DatabaseError):  # 이미 래핑된 예외는 다시 래핑하지 않음
                error_msg = f"Database error while saving entity"
                self.logger.error(error_msg, 
                             table=self.schema.table_name, 
                             entity=str(entity), 
                             error=str(e))
                raise DatabaseError(f"{error_msg} in {self.schema.table_name}: {str(e)}")
            raise e
    
    def _insert(self, entity: T) -> T:
        """엔티티 추가
        
        Args:
            entity: 추가할 엔티티
            
        Returns:
            추가된 엔티티
            
        Raises:
            DatabaseError: 데이터베이스 추가 중 오류 발생 시
        """
        try:
            query = self.schema.insert_sql()
            params = self.schema.get_insert_params(entity)
            
            self.logger.debug(f"Inserting entity", 
                         table=self.schema.table_name, 
                         id=getattr(entity, self.schema.primary_key.name))
            
            self.db.execute_query(query, params)
            
            self.logger.info(f"Entity created", 
                        table=self.schema.table_name,
                        id=getattr(entity, self.schema.primary_key.name),
                        name=getattr(entity, 'name', None))
            
            return entity
            
        except Exception as e:
            error_msg = f"Database error while inserting entity"
            self.logger.error(error_msg, 
                         table=self.schema.table_name, 
                         entity=str(entity), 
                         error=str(e))
            raise DatabaseError(f"{error_msg} in {self.schema.table_name}: {str(e)}")
    
    def _update(self, entity: T) -> T:
        """엔티티 수정
        
        Args:
            entity: 수정할 엔티티
            
        Returns:
            수정된 엔티티
            
        Raises:
            DatabaseError: 데이터베이스 수정 중 오류 발생 시
        """
        try:
            query = self.schema.update_sql()
            params = self.schema.get_update_params(entity)
            
            self.logger.debug(f"Updating entity", 
                         table=self.schema.table_name, 
                         id=getattr(entity, self.schema.primary_key.name))
            
            self.db.execute_query(query, params)
            
            self.logger.info(f"Entity updated", 
                        table=self.schema.table_name,
                        id=getattr(entity, self.schema.primary_key.name),
                        name=getattr(entity, 'name', None))
            
            return entity
            
        except Exception as e:
            error_msg = f"Database error while updating entity"
            self.logger.error(error_msg, 
                         table=self.schema.table_name, 
                         entity=str(entity), 
                         error=str(e))
            raise DatabaseError(f"{error_msg} in {self.schema.table_name}: {str(e)}")
    
    def delete(self, id_value: str) -> bool:
        """엔티티 삭제
        
        Args:
            id_value: 삭제할 엔티티 ID
            
        Returns:
            삭제 성공 여부
            
        Raises:
            DatabaseError: 데이터베이스 삭제 중 오류 발생 시
        """
        try:
            # 엔티티 존재 확인 - 원래대로 복구
            exists = self.exists_by_id(id_value)
            
            if not exists:
                self.logger.warning(f"Cannot delete: Entity not found", 
                               table=self.schema.table_name, 
                               id=id_value)
                return False
            
            query = self.schema.delete_sql()
            
            self.logger.debug(f"Deleting entity", 
                         table=self.schema.table_name, 
                         id=id_value)
            
            self.db.execute_query(query, (id_value,))
            
            self.logger.info(f"Entity deleted", 
                        table=self.schema.table_name, 
                        id=id_value)
            
            return True
            
        except Exception as e:
            error_msg = f"Database error while deleting entity"
            self.logger.error(error_msg, 
                         table=self.schema.table_name, 
                         id=id_value, 
                         error=str(e))
            raise DatabaseError(f"{error_msg} in {self.schema.table_name}: {str(e)}")
    
    def _map_to_entity(self, row: Dict[str, Any]) -> T:
        """DB 로우를 엔티티로 변환
        
        Args:
            row: DB 조회 결과 로우
            
        Returns:
            변환된 엔티티
        """
        # 원래 코드로 복구
        return self.entity_class(**row) 