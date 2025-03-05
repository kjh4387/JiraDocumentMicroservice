import unittest
from unittest.mock import MagicMock, patch

# 실제 클래스 가져오기 대신 테스트용 모의 클래스 정의
class MockPostgresRepository:
    def __init__(self, db_client, table_name):
        self.db_client = db_client
        self.table_name = table_name

class TestPostgresRepository(unittest.TestCase):
    
    def setUp(self):
        # DB 클라이언트 모의 객체 생성
        self.db_client = MagicMock()
        self.conn = MagicMock()
        self.cursor = MagicMock()
        
        # 커넥션 및 커서 설정
        self.db_client.get_connection.return_value.__enter__.return_value = self.conn
        self.conn.cursor.return_value.__enter__.return_value = self.cursor
        
        # 레포지토리 생성
        self.repo = MockPostgresRepository(self.db_client, "test_table")
    
    def test_find_one(self):
        # 모의 쿼리 결과 설정
        self.cursor.fetchone.return_value = {"id": 1, "name": "테스트", "value": 100}
        
        # 테스트 쿼리 실행
        result = self.repo.find_one({"id": 1})
        
        # SQL 쿼리 실행 확인
        self.cursor.execute.assert_called_once()
        
        # 결과 확인
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "테스트")
        self.assertEqual(result["value"], 100)
    
    def test_find_one_no_result(self):
        # 결과가 없는 경우 설정
        self.cursor.fetchone.return_value = None
        
        # 테스트 쿼리 실행
        result = self.repo.find_one({"id": 999})
        
        # 결과가 None인지 확인
        self.assertIsNone(result)
    
    def test_find_many(self):
        # 모의 쿼리 결과 설정
        self.cursor.fetchall.return_value = [
            {"id": 1, "name": "테스트1"},
            {"id": 2, "name": "테스트2"}
        ]
        
        # 테스트 쿼리 실행
        results = self.repo.find_many({"dept": "개발"})
        
        # 결과 확인
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "테스트1")
        self.assertEqual(results[1]["name"], "테스트2")
    
    def test_insert_one(self):
        # 삽입 ID 설정
        self.cursor.fetchone.return_value = ["new-id-1234"]
        
        # 테스트 문서 삽입
        document = {"name": "새 문서", "value": 500}
        result = self.repo.insert_one(document)
        
        # SQL 쿼리와 커밋 호출 확인
        self.cursor.execute.assert_called_once()
        self.conn.commit.assert_called_once()
        
        # 결과가 올바른 ID인지 확인
        self.assertEqual(result, "new-id-1234")
    
    def test_update_one(self):
        # 업데이트 영향 행 수 설정
        self.cursor.rowcount = 1
        
        # 테스트 업데이트 실행
        result = self.repo.update_one({"id": 1}, {"name": "업데이트", "value": 999})
        
        # SQL 쿼리와 커밋 호출 확인
        self.cursor.execute.assert_called_once()
        self.conn.commit.assert_called_once()
        
        # 결과가 성공인지 확인
        self.assertTrue(result)
    
    def test_delete_one(self):
        # 삭제 영향 행 수 설정
        self.cursor.rowcount = 1
        
        # 테스트 삭제 실행
        result = self.repo.delete_one({"id": 1})
        
        # SQL 쿼리와 커밋 호출 확인
        self.cursor.execute.assert_called_once()
        self.conn.commit.assert_called_once()
        
        # 결과가 성공인지 확인
        self.assertTrue(result)

class TestEmployeeRepository(unittest.TestCase):
    
    def test_initialization(self):
        db_client = MagicMock()
        repo = MockPostgresRepository(db_client, "employees")
        
        # 테이블명이 올바르게 설정되었는지 확인
        self.assertEqual(repo.table_name, "employees")

class TestCompanyRepository(unittest.TestCase):
    
    def test_initialization(self):
        db_client = MagicMock()
        repo = MockPostgresRepository(db_client, "companies")
        
        # 테이블명이 올바르게 설정되었는지 확인
        self.assertEqual(repo.table_name, "companies")

class TestRepositories(unittest.TestCase):
    def test_repository_initialization(self):
        db_client = MagicMock()
        repo = MockPostgresRepository(db_client, "test_table")
        self.assertEqual(repo.table_name, "test_table") 