import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Tuple, Optional
from app.source.core.interfaces import UnitOfWork
from app.source.core.exceptions import DatabaseError
import logging

class DatabaseConnection:
    """데이터베이스 연결 클래스"""
    
    def __init__(self, config: dict, logger: Optional[logging.Logger] = None):
        self.config = config
        self.connection = None
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("DatabaseConnection initialized")
    
    def connect(self):
        """데이터베이스 연결"""
        if not self.connection:
            try:
                self.connection = psycopg2.connect(
                    host=self.config.get("host"),
                    user=self.config.get("user"),
                    password=self.config.get("password"),
                    dbname=self.config.get("database"),
                    port=self.config.get("port", 5432)
                )
                self.logger.debug("Database connection established")
            except Exception as e:
                self.logger.error("Database connection failed: %s", str(e))
                raise DatabaseError(f"Database connection failed: {str(e)}")
        return self.connection
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                self.logger.debug("Database connection closed")
            except Exception as e:
                self.logger.error("Failed to close database connection: %s", str(e))
                raise DatabaseError(f"Failed to close database connection: {str(e)}")
    
    def execute_query(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """쿼리 실행 및 결과 반환"""
        conn = self.connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            self.logger.debug("Executing query: %s, params: %s", query, params)
            cursor.execute(query, params)
            
            # SELECT 쿼리인 경우 결과 반환
            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
                # DictCursor 결과를 일반 딕셔너리로 변환
                result = [dict(row) for row in result]
                self.logger.debug("Query executed successfully, rows affected: %d", len(result))
                return result
            
            # INSERT, UPDATE, DELETE 쿼리인 경우 커밋
            conn.commit()
            self.logger.debug("Query executed successfully, rows affected: %d", cursor.rowcount)
            return []
        except Exception as e:
            conn.rollback()
            self.logger.error("Query execution failed: %s (query: %s, params: %s)", str(e), query, params)
            raise DatabaseError(f"Query execution failed: {str(e)}")
        finally:
            cursor.close()
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """여러 쿼리 실행"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            self.logger.debug("Executing multiple queries: %s, params count: %d", query, len(params_list))
            cursor.executemany(query, params_list)
            conn.commit()
            self.logger.debug("Multiple queries executed successfully, rows affected: %d", cursor.rowcount)
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            self.logger.error("Multiple query execution failed: %s (query: %s)", str(e), query)
            raise DatabaseError(f"Multiple query execution failed: {str(e)}")
        finally:
            cursor.close()

class DatabaseUnitOfWork(UnitOfWork):
    """데이터베이스 단위 작업 구현"""
    
    def __init__(self, connection: DatabaseConnection, logger: Optional[logging.Logger] = None):
        self.connection = connection
        self.logger = logger or logging.getLogger(__name__)
        self._transaction = None
    
    def __enter__(self):
        """트랜잭션 시작"""
        self.connection.connect()
        self.connection.autocommit = False
        self.logger.debug("Transaction started")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """트랜잭션 종료"""
        if exc_type:
            self.rollback()
            self.logger.warning("Transaction rolled back due to exception: %s (%s)", 
                          exc_type.__name__, str(exc_val))
        else:
            self.commit()
            self.logger.debug("Transaction committed")
        
        self.connection.autocommit = True
    
    def commit(self):
        """변경사항 커밋"""
        self.connection.commit()
        self.logger.debug("Changes committed")
    
    def rollback(self):
        """변경사항 롤백"""
        self.connection.rollback()
        self.logger.debug("Changes rolled back")
