from typing import Dict, Any, List, Optional
from core.interfaces import Repository
from core.domain import Company
from core.exceptions import EntityNotFoundError, DatabaseError
from core.logging import get_logger
from infrastructure.persistence.db_connection import DatabaseConnection

logger = get_logger(__name__)

class CompanyRepository(Repository[Company]):
    """회사 정보 저장소"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        logger.debug("CompanyRepository initialized")
    
    def find_by_id(self, id: str) -> Optional[Company]:
        """ID로 회사 조회"""
        logger.debug("Finding company by ID", id=id)
        query = "SELECT * FROM companies WHERE id = %s"
        
        try:
            result = self.db.execute_query(query, (id,))
            
            if not result:
                logger.warning("Company not found", id=id)
                return None
            
            company = Company(**result[0])
            logger.debug("Company found", id=id, company_name=company.company_name)
            return company
        except Exception as e:
            logger.error("Database error while finding company", id=id, error=str(e))
            raise DatabaseError(f"Failed to find company with ID {id}: {str(e)}")
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Company]:
        """조건에 맞는 회사 목록 조회"""
        logger.debug("Finding companies by criteria", criteria=criteria)
        conditions = []
        params = []
        
        for key, value in criteria.items():
            conditions.append(f"{key} = %s")  # PostgreSQL에서는 %s 사용
            params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM companies WHERE {where_clause}"
        
        try:
            results = self.db.execute_query(query, tuple(params))
            companies = [Company(**row) for row in results]
            logger.debug("Companies found", count=len(companies))
            return companies
        except Exception as e:
            logger.error("Database error while finding companies by criteria", criteria=criteria, error=str(e))
            raise DatabaseError(f"Failed to find companies by criteria: {str(e)}")
    
    def find_by_name(self, name: str) -> Optional[Company]:
        """회사명으로 회사 조회"""
        logger.debug("Finding company by name", name=name)
        query = "SELECT * FROM companies WHERE company_name = %s"
        try:
            result = self.db.execute_query(query, (name,))
            
            if not result:
                logger.warning("Company not found", name=name)
                return None
            
            company = Company(**result[0])
            logger.debug("Company found", id=company.id, company_name=company.company_name)
            return company
        except Exception as e:
            logger.error("Database error while finding company by name", name=name, error=str(e))
            raise DatabaseError(f"Failed to find company by name {name}: {str(e)}")
    
    def save(self, company: Company) -> Company:
        """회사 정보 저장"""
        logger.debug("Saving company", id=company.id, company_name=company.company_name)
        
        # 기존 회사 확인
        existing = self.find_by_id(company.id)
        
        if existing:
            # 업데이트
            query = """
                UPDATE companies 
                SET company_name = %s, biz_id = %s, rep_name = %s, address = %s,
                    biz_type = %s, biz_item = %s, phone = %s, rep_stamp = %s
                WHERE id = %s
            """
            params = (
                company.company_name, company.biz_id, company.rep_name, company.address,
                company.biz_type, company.biz_item, company.phone, company.rep_stamp,
                company.id
            )
            try:
                self.db.execute_query(query, params)
                logger.info("Company updated", id=company.id, company_name=company.company_name)
            except Exception as e:
                logger.error("Database error while updating company", id=company.id, error=str(e))
                raise DatabaseError(f"Failed to update company {company.id}: {str(e)}")
        else:
            # 삽입
            query = """
                INSERT INTO companies 
                (id, company_name, biz_id, rep_name, address, biz_type, biz_item, phone, rep_stamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                company.id, company.company_name, company.biz_id, company.rep_name, company.address,
                company.biz_type, company.biz_item, company.phone, company.rep_stamp
            )
            try:
                self.db.execute_query(query, params)
                logger.info("Company created", id=company.id, company_name=company.company_name)
            except Exception as e:
                logger.error("Database error while creating company", id=company.id, error=str(e))
                raise DatabaseError(f"Failed to create company {company.id}: {str(e)}")
        
        return company
    
    def delete(self, id: str) -> bool:
        """회사 정보 삭제"""
        logger.debug("Deleting company", id=id)
        
        # 기존 회사 확인
        existing = self.find_by_id(id)
        
        if not existing:
            logger.warning("Cannot delete: Company not found", id=id)
            return False
        
        query = "DELETE FROM companies WHERE id = %s"
        try:
            self.db.execute_query(query, (id,))
            logger.info("Company deleted", id=id)
            return True
        except Exception as e:
            logger.error("Database error while deleting company", id=id, error=str(e))
            raise DatabaseError(f"Failed to delete company {id}: {str(e)}")
