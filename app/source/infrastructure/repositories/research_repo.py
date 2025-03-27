from typing import Dict, Any, List, Optional
from app.source.core.interfaces import Repository
from app.source.core.domain import Research
from app.source.core.exceptions import EntityNotFoundError, DatabaseError
import logging
from app.source.infrastructure.persistence.db_connection import DatabaseConnection

class ResearchRepository(Repository[Research]):
    """연구 과제 정보 저장소"""
    
    def __init__(self, db_connection: DatabaseConnection, logger: Optional[logging.Logger] = None):
        self.db = db_connection
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("ResearchRepository initialized")
    
    def find_by_id(self, id: str) -> Optional[Research]:
        """ID로 연구 과제 조회"""
        self.logger.debug("Finding research project by ID", id=id)
        query = "SELECT * FROM research_projects WHERE id = %s"
        
        try:
            result = self.db.execute_query(query, (id,))
            
            if not result:
                self.logger.warning("Research project not found", id=id)
                return None
            
            research = Research(**result[0])
            self.logger.debug("Research project found", id=id, project_name=research.project_name)
            return research
        except Exception as e:
            self.logger.error("Database error while finding research project", id=id, error=str(e))
            raise DatabaseError(f"Failed to find research project with ID {id}: {str(e)}")
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Research]:
        """조건에 맞는 연구 과제 목록 조회"""
        self.logger.debug("Finding research projects by criteria", criteria=criteria)
        conditions = []
        params = []
        
        for key, value in criteria.items():
            conditions.append(f"{key} = %s")
            params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM research_projects WHERE {where_clause}"
        
        try:
            results = self.db.execute_query(query, tuple(params))
            projects = [Research(**row) for row in results]
            self.logger.debug("Research projects found", count=len(projects))
            return projects
        except Exception as e:
            self.logger.error("Database error while finding research projects by criteria", criteria=criteria, error=str(e))
            raise DatabaseError(f"Failed to find research projects by criteria: {str(e)}")
    
    def find_by_manager(self, manager: str) -> List[Research]:
        """프로젝트 매니저로 연구 과제 목록 조회"""
        self.logger.debug("Finding research projects by manager", manager=manager)
        query = "SELECT * FROM research_projects WHERE project_manager = %s"
        
        try:
            results = self.db.execute_query(query, (manager,))
            projects = [Research(**row) for row in results]
            self.logger.debug("Research projects found", count=len(projects), manager=manager)
            return projects
        except Exception as e:
            self.logger.error("Database error while finding research projects by manager", manager=manager, error=str(e))
            raise DatabaseError(f"Failed to find research projects by manager {manager}: {str(e)}")
    
    def save(self, research: Research) -> Research:
        """연구 과제 정보 저장"""
        self.logger.debug("Saving research project", id=research.id, project_name=research.project_name)
        
        # 기존 연구 과제 확인
        existing = self.find_by_id(research.id)
        
        if existing:
            # 업데이트
            query = """
                UPDATE research_projects 
                SET project_name = %s, project_code = %s, project_period = %s, 
                    project_manager = %s, project_start_date = %s, project_end_date = %s,
                    budget = %s, status = %s, description = %s
                WHERE id = %s
            """
            params = (
                research.project_name, research.project_code, research.project_period,
                research.project_manager, research.project_start_date, research.project_end_date,
                research.budget, research.status, research.description, research.id
            )
            try:
                self.db.execute_query(query, params)
                self.logger.info("Research project updated", id=research.id, project_name=research.project_name)
            except Exception as e:
                self.logger.error("Database error while updating research project", id=research.id, error=str(e))
                raise DatabaseError(f"Failed to update research project {research.id}: {str(e)}")
        else:
            # 삽입
            query = """
                    INSERT INTO research_projects 
                    (id, project_name, project_code, project_period, project_manager, project_start_date, project_end_date, budget, status, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                research.id, research.project_name, research.project_code, research.project_period,
                research.project_manager, research.project_start_date, research.project_end_date, research.budget, research.status, research.description
            )
            try:
                self.db.execute_query(query, params)
                self.logger.info("Research project created", id=research.id, project_name=research.project_name)
            except Exception as e:
                self.logger.error("Database error while creating research project", id=research.id, error=str(e))
                raise DatabaseError(f"Failed to create research project {research.id}: {str(e)}")
        
        return research
    
    def delete(self, id: str) -> bool:
        """연구 과제 정보 삭제"""
        self.logger.debug("Deleting research project", id=id)
        
        # 기존 연구 과제 확인
        existing = self.find_by_id(id)
        
        if not existing:
            self.logger.warning("Cannot delete: Research project not found", id=id)
            return False
        
        query = "DELETE FROM research_projects WHERE id = %s"
        try:
            self.db.execute_query(query, (id,))
            self.logger.info("Research project deleted", id=id)
            return True
        except Exception as e:
            self.logger.error("Database error while deleting research project", id=id, error=str(e))
            raise DatabaseError(f"Failed to delete research project {id}: {str(e)}")

    def find_by_project_code(self, project_code: str) -> Optional[Research]:
        """프로젝트 코드로 연구 과제 조회"""
        self.logger.debug("Finding research by project code", project_code=project_code)
        query = "SELECT * FROM research_projects WHERE project_code = %s"
        
        try:
            result = self.db.execute_query(query, (project_code,))
            
            if not result:
                self.logger.warning("Research project not found", project_code=project_code)
                return None
            
            research = Research(**result[0])
            self.logger.debug("Research project found", id=research.id, project_name=research.project_name)
            return research
        except Exception as e:
            self.logger.error("Database error while finding research by project code", project_code=project_code, error=str(e))
            raise DatabaseError(f"Failed to find research with project code {project_code}: {str(e)}")
