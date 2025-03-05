import unittest
from unittest.mock import MagicMock, patch
from app.source.infrastructure.counter_service import CounterService

class TestCounterService(unittest.TestCase):
    
    def setUp(self):
        # DB 클라이언트 모의 객체 생성
        self.db_client = MagicMock()
        self.conn = MagicMock()
        self.cursor = MagicMock()
        
        # 커넥션 및 커서 설정
        self.db_client.get_connection.return_value.__enter__.return_value = self.conn
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        
        # 카운터 서비스 생성
        self.counter_service = CounterService(self.db_client)
    
    def test_ensure_counter_table(self):
        # 메서드가 초기화 중에 호출되었는지 확인
        self.cursor.execute.assert_called_once()
        self.conn.commit.assert_called_once()
    
    def test_get_next_counter(self):
        # 테스트 설정 초기화 호출에서 이미 사용된 카운트 초기화
        self.cursor.execute.reset_mock()
        self.conn.commit.reset_mock()
        
        # 시퀀스 결과 설정
        self.cursor.fetchone.return_value = [42]
        
        # 테스트 카운터 값 요청
        result = self.counter_service.get_next_counter("문서유형", 2023)
        
        # SQL 쿼리 실행 확인
        self.cursor.execute.assert_called_once()
        self.assertTrue("INSERT INTO counters" in str(self.cursor.execute.call_args))
        self.assertTrue("문서유형_2023" in str(self.cursor.execute.call_args))
        
        # 결과가 올바른지 확인
        self.assertEqual(result, 42)
    
    def test_get_next_counter_exception(self):
        # 테스트 설정 초기화 호출에서 이미 사용된 카운트 초기화
        self.cursor.execute.reset_mock()
        self.conn.commit.reset_mock()
        
        # 예외 발생 설정
        self.cursor.execute.side_effect = Exception("테스트 예외")
        
        # 테스트 카운터 값 요청 - 예외 발생해도 기본값 반환해야 함
        result = self.counter_service.get_next_counter("문서유형", 2023)
        
        # 기본값 999가 반환되는지 확인
        self.assertEqual(result, 999) 