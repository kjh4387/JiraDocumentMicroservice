from typing import Dict, Any
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class CounterService:
    """문서 번호 등을 위한 카운터 서비스"""
    
    def __init__(self, db_client):
        self.db_client = db_client
        # 카운터 테이블이 없으면 생성
        self._ensure_counter_table()
        logger.debug("Initialized counter service")
    
    def _ensure_counter_table(self):
        """카운터 테이블 생성 확인"""
        try:
            with self.db_client.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS counters (
                            counter_id VARCHAR(100) PRIMARY KEY,
                            seq INTEGER NOT NULL DEFAULT 1
                        )
                    """)
                    conn.commit()
        except Exception as e:
            logger.error("Failed to create counter table", error=str(e))
    
    def get_next_counter(self, counter_type: str, year: int) -> int:
        """다음 카운터 값 가져오기"""
        counter_id = f"{counter_type}_{year}"
        
        try:
            with self.db_client.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 카운터가 없으면 생성하고 1을 반환, 있으면 증가시키고 새 값 반환
                    cursor.execute("""
                        INSERT INTO counters (counter_id, seq)
                        VALUES (%s, 1)
                        ON CONFLICT (counter_id) DO UPDATE
                        SET seq = counters.seq + 1
                        RETURNING seq
                    """, (counter_id,))
                    
                    result = cursor.fetchone()
                    conn.commit()
                    
                    return result[0]
        except Exception as e:
            logger.error(f"Failed to get next counter", 
                       counter_type=counter_type, 
                       year=year, 
                       error=str(e))
            # 실패 시 임시 값 반환 (실제 운영에서는 적절한 에러 처리 필요)
            return 999 