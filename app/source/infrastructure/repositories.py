from typing import Dict, Any, List, Optional
from app.source.core.interfaces import Repository
from app.source.core.logging import get_logger
import psycopg2
import psycopg2.extras
import json

logger = get_logger(__name__)

class PostgresRepository(Repository):
    """PostgreSQL 기반 레포지토리 구현체"""
    
    def __init__(self, db_client, table_name: str):
        self.db_client = db_client
        self.table_name = table_name
        logger.debug(f"Initialized PostgreSQL repository", table=table_name)
    
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """단일 문서 조회"""
        try:
            # 단순 쿼리 변환 (정교한 구현은 필요에 따라 개선 필요)
            conditions = []
            params = []
            
            for key, value in query.items():
                conditions.append(f"{key} = %s")
                params.append(value)
                
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} LIMIT 1"
            
            with self.db_client.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(sql, params)
                    result = cursor.fetchone()
                    
                    if result:
                        # dict로 변환
                        return dict(result)
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to find document", query=query, error=str(e))
            return None
    
    def find_many(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """여러 문서 조회"""
        try:
            # 단순 쿼리 변환
            conditions = []
            params = []
            
            for key, value in query.items():
                conditions.append(f"{key} = %s")
                params.append(value)
                
            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            
            sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} LIMIT %s"
            params.append(limit)
            
            with self.db_client.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(sql, params)
                    results = cursor.fetchall()
                    
                    # dict 리스트로 변환
                    return [dict(row) for row in results]
                    
        except Exception as e:
            logger.error(f"Failed to find documents", query=query, error=str(e))
            return []
    
    def insert_one(self, document: Dict[str, Any]) -> str:
        """단일 문서 저장"""
        try:
            columns = list(document.keys())
            values = list(document.values())
            
            placeholders = ["%s"] * len(columns)
            
            sql = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
            
            with self.db_client.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    result = cursor.fetchone()
                    conn.commit()
                    
                    return str(result[0])
                    
        except Exception as e:
            logger.error(f"Failed to insert document", error=str(e))
            raise
    
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """단일 문서 업데이트"""
        try:
            # WHERE 절 구성
            where_conditions = []
            where_params = []
            
            for key, value in query.items():
                where_conditions.append(f"{key} = %s")
                where_params.append(value)
                
            where_clause = " AND ".join(where_conditions)
            
            # SET 절 구성
            set_clauses = []
            set_params = []
            
            for key, value in update.items():
                set_clauses.append(f"{key} = %s")
                set_params.append(value)
                
            set_clause = ", ".join(set_clauses)
            
            sql = f"UPDATE {self.table_name} SET {set_clause} WHERE {where_clause}"
            params = set_params + where_params
            
            with self.db_client.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    affected_rows = cursor.rowcount
                    conn.commit()
                    
                    return affected_rows > 0
                    
        except Exception as e:
            logger.error(f"Failed to update document", query=query, error=str(e))
            return False
    
    def delete_one(self, query: Dict[str, Any]) -> bool:
        """단일 문서 삭제"""
        try:
            # WHERE 절 구성
            where_conditions = []
            where_params = []
            
            for key, value in query.items():
                where_conditions.append(f"{key} = %s")
                where_params.append(value)
                
            where_clause = " AND ".join(where_conditions)
            
            sql = f"DELETE FROM {self.table_name} WHERE {where_clause} LIMIT 1"
            
            with self.db_client.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, where_params)
                    affected_rows = cursor.rowcount
                    conn.commit()
                    
                    return affected_rows > 0
                    
        except Exception as e:
            logger.error(f"Failed to delete document", query=query, error=str(e))
            return False


class EmployeeRepository(PostgresRepository):
    """직원 정보 레포지토리"""
    
    def __init__(self, db_client):
        super().__init__(db_client, "employees")


class CompanyRepository(PostgresRepository):
    """회사 정보 레포지토리"""
    
    def __init__(self, db_client):
        super().__init__(db_client, "companies")


class ProjectRepository(PostgresRepository):
    """프로젝트 정보 레포지토리"""
    
    def __init__(self, db_client):
        super().__init__(db_client, "projects")


class ExpertRepository(PostgresRepository):
    """전문가 정보 레포지토리"""
    
    def __init__(self, db_client):
        super().__init__(db_client, "experts") 