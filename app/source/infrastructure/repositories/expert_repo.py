from typing import Dict, Any, List, Optional
from app.source.core.interfaces import Repository
from app.source.core.domain import Expert
from app.source.core.exceptions import EntityNotFoundError, DatabaseError
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class ExpertRepository(Repository[Expert]):
    """전문가 정보 저장소"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        logger.debug("ExpertRepository initialized")
    
    def find_by_id(self, id: str) -> Optional[Expert]:
        """ID로 전문가 조회"""
        logger.debug("Finding expert by ID", id=id)
        query = "SELECT * FROM experts WHERE id = %s"
        
        try:
            result = self.db.execute_query(query, (id,))
            
            if not result:
                logger.warning("Expert not found", id=id)
                return None
            
            expert = Expert(**result[0])
            logger.debug("Expert found", id=id, name=expert.name)
            return expert
        except Exception as e:
            logger.error("Database error while finding expert", id=id, error=str(e))
            raise DatabaseError(f"Failed to find expert with ID {id}: {str(e)}")
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Expert]:
        """조건에 맞는 전문가 목록 조회"""
        logger.debug("Finding experts by criteria", criteria=criteria)
        conditions = []
        params = []
        
        for key, value in criteria.items():
            conditions.append(f"{key} = %s")
            params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM experts WHERE {where_clause}"
        
        try:
            results = self.db.execute_query(query, tuple(params))
            experts = [Expert(**row) for row in results]
            logger.debug("Experts found", count=len(experts))
            return experts
        except Exception as e:
            logger.error("Database error while finding experts by criteria", criteria=criteria, error=str(e))
            raise DatabaseError(f"Failed to find experts by criteria: {str(e)}")
    
    def find_by_name(self, name: str) -> List[Expert]:
        """이름으로 전문가 조회"""
        logger.debug("Finding experts by name", name=name)
        query = "SELECT * FROM experts WHERE name LIKE %s"
        
        try:
            result = self.db.execute_query(query, (f"%{name}%",))
            experts = [Expert(**row) for row in result]
            logger.debug("Experts found", count=len(experts), name=name)
            return experts
        except Exception as e:
            logger.error("Database error while finding experts by name", name=name, error=str(e))
            raise DatabaseError(f"Failed to find experts by name {name}: {str(e)}")
    
    def save(self, expert: Expert) -> Expert:
        """전문가 정보 저장"""
        logger.debug("Saving expert", id=expert.id, name=expert.name)
        
        # 기존 전문가 확인
        existing = self.find_by_id(expert.id)
        
        if existing:
            # 업데이트
            query = """
                UPDATE experts 
                SET name = %s, affiliation = %s, position = %s, birth_date = %s,
                    address = %s, email = %s, phone = %s,
                    bank_name = %s, account_number = %s, specialty = %s, bio = %s
                WHERE id = %s
            """
            params = (
                expert.name, expert.affiliation, expert.position, expert.birth_date,
                expert.address, expert.email, expert.phone,
                expert.bank_name, expert.account_number, expert.specialty, expert.bio,
                expert.id
            )
            try:
                self.db.execute_query(query, params)
                logger.info("Expert updated", id=expert.id, name=expert.name)
            except Exception as e:
                logger.error("Database error while updating expert", id=expert.id, error=str(e))
                raise DatabaseError(f"Failed to update expert {expert.id}: {str(e)}")
        else:
            # 삽입
            query = """
                INSERT INTO experts 
                (id, name, affiliation, position, birth_date, address, email, phone, bank_name, account_number, specialty, bio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                expert.id, expert.name, expert.affiliation, expert.position, expert.birth_date,
                expert.address, expert.email, expert.phone,
                expert.bank_name, expert.account_number, expert.specialty, expert.bio
            )
            try:
                self.db.execute_query(query, params)
                logger.info("Expert created", id=expert.id, name=expert.name)
            except Exception as e:
                logger.error("Database error while creating expert", id=expert.id, error=str(e))
                raise DatabaseError(f"Failed to create expert {expert.id}: {str(e)}")
        
        return expert
    
    def delete(self, id: str) -> bool:
        """전문가 정보 삭제"""
        logger.debug("Deleting expert", id=id)
        
        # 기존 전문가 확인
        existing = self.find_by_id(id)
        
        if not existing:
            logger.warning("Cannot delete: Expert not found", id=id)
            return False
        
        query = "DELETE FROM experts WHERE id = %s"
        try:
            self.db.execute_query(query, (id,))
            logger.info("Expert deleted", id=id)
            return True
        except Exception as e:
            logger.error("Database error while deleting expert", id=id, error=str(e))
            raise DatabaseError(f"Failed to delete expert {id}: {str(e)}")
