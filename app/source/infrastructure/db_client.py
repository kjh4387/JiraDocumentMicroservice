import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from app.source.core.logging import get_logger
import os

logger = get_logger(__name__)

class DatabaseClient:
    """PostgreSQL 데이터베이스 클라이언트"""
    
    def __init__(self, connection_params: dict):
        self.connection_params = connection_params
        self.pool = None
        self._connect()
    
    def _connect(self):
        """데이터베이스 연결"""
        try:
            self.pool = SimpleConnectionPool(1, 20, **self.connection_params)
            logger.info("Connected to PostgreSQL database", 
                       db_name=self.connection_params.get("dbname"))
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise
    
    @contextmanager
    def get_connection(self):
        """커넥션 풀에서 연결 가져오기"""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    def close(self):
        """연결 종료"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


def get_db_client():
    """데이터베이스 클라이언트 인스턴스 생성"""
    connection_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "document_system"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres")
    }
    return DatabaseClient(connection_params) 