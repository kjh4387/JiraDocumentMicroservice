"""
직원 레포지토리 V2 테스트
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional

from app.source.core.domain import Employee
from app.source.core.exceptions import DatabaseError
from app.source.infrastructure.repositories.employee_repo_v2 import EmployeeRepositoryV2
from app.source.infrastructure.persistence.schema_definition import TableSchema, ColumnDefinition

class TestEmployeeRepositoryV2(unittest.TestCase):
    """직원 레포지토리 V2 테스트"""
    
    def setUp(self):
        """테스트 사전 설정"""
        # 모의 DB 연결 객체 생성
        self.mock_db = Mock()
        
        # 모의 로거 생성
        self.mock_logger = Mock()
        
        # 테스트용 스키마 생성
        self.schema = TableSchema(
            table_name="employees",
            columns=[
                ColumnDefinition(name="id", data_type="VARCHAR(50)", primary_key=True),
                ColumnDefinition(name="name", data_type="VARCHAR(100)", nullable=False),
                ColumnDefinition(name="email", data_type="VARCHAR(100)", nullable=False),
                ColumnDefinition(name="department", data_type="VARCHAR(100)"),
                ColumnDefinition(name="position", data_type="VARCHAR(100)"),
                ColumnDefinition(name="jira_account_id", data_type="VARCHAR(100)")
            ],
            logger=self.mock_logger
        )
        
        # 패치 적용
        self.schema_registry_patch = patch('app.source.infrastructure.persistence.schema_definition.SchemaRegistry.get')
        self.mock_schema_registry = self.schema_registry_patch.start()
        self.mock_schema_registry.return_value = self.schema
        
        # 레포지토리 인스턴스 생성
        self.repo = EmployeeRepositoryV2(self.mock_db, logger=self.mock_logger)
        
        # 테스트 샘플 데이터
        self.test_employee = Employee(
            id="EMP-001",
            name="홍길동",
            email="hong@example.com",
            department="개발팀",
            position="선임 개발자",
            jira_account_id="jira123"
        )
        self.test_row = {
            "id": "EMP-001",
            "name": "홍길동",
            "email": "hong@example.com",
            "department": "개발팀",
            "position": "선임 개발자",
            "jira_account_id": "jira123"
        }
        
    def tearDown(self):
        """테스트 후 정리"""
        self.schema_registry_patch.stop()
    
    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.repo.schema, self.schema)
        self.assertEqual(self.repo.db, self.mock_db)
        self.assertEqual(self.repo.entity_class, Employee)
    
    def test_find_by_id(self):
        """ID로 검색 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [self.test_row]
        
        # 메서드 호출
        result = self.repo.find_by_id("EMP-001")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(result.id, self.test_employee.id)
        self.assertEqual(result.name, self.test_employee.name)
        self.assertEqual(result.email, self.test_employee.email)
        self.assertEqual(result.jira_account_id, self.test_employee.jira_account_id)
    
    def test_find_by_id_not_found(self):
        """ID로 검색 - 결과 없음 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = []
        
        # 메서드 호출
        result = self.repo.find_by_id("EMP-999")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertIsNone(result)
    
    def test_find_by_id_db_error(self):
        """ID로 검색 - 데이터베이스 오류 테스트"""
        # mock 설정
        self.mock_db.execute_query.side_effect = Exception("DB Connection Error")
        
        # 메서드 호출 및 예외 검증
        with self.assertRaises(DatabaseError):
            self.repo.find_by_id("EMP-001")
    
    def test_find_by_email(self):
        """이메일로 검색 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [self.test_row]
        
        # 메서드 호출
        result = self.repo.find_by_email("hong@example.com")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(result.id, self.test_employee.id)
        self.assertEqual(result.email, self.test_employee.email)
    
    def test_find_by_email_not_found(self):
        """이메일로 검색 - 결과 없음 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = []
        
        # 메서드 호출
        result = self.repo.find_by_email("unknown@example.com")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertIsNone(result)
    
    def test_find_by_jira_account_id(self):
        """Jira account ID로 검색 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [self.test_row]
        
        # 메서드 호출
        result = self.repo.find_by_jira_account_id("jira123")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(result.id, self.test_employee.id)
        self.assertEqual(result.jira_account_id, self.test_employee.jira_account_id)
    
    def test_find_by_jira_account_id_not_found(self):
        """Jira account ID로 검색 - 결과 없음 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = []
        
        # 메서드 호출
        result = self.repo.find_by_jira_account_id("unknown123")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertIsNone(result)
    
    def test_find_by_department(self):
        """부서로 검색 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [self.test_row]
        
        # 메서드 호출
        result = self.repo.find_by_department("개발팀")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, self.test_employee.id)
        self.assertEqual(result[0].department, self.test_employee.department)
    
    def test_search(self):
        """키워드 검색 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [self.test_row]
        
        # 메서드 호출
        result = self.repo.search("홍길동")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, self.test_employee.id)
        self.assertEqual(result[0].name, self.test_employee.name)
    
    def test_save_insert(self):
        """저장 (삽입) 테스트"""
        # mock 설정
        self.mock_db.execute_query.side_effect = [[], None]  # exists_by_id=False, _insert
        
        # 메서드 호출
        self.repo.save(self.test_employee)
        
        # 검증
        self.assertEqual(self.mock_db.execute_query.call_count, 2)
    
    def test_save_update(self):
        """저장 (업데이트) 테스트"""
        # mock 설정
        self.mock_db.execute_query.side_effect = [[self.test_row], None]  # exists_by_id=True, _update
        
        # 메서드 호출
        self.repo.save(self.test_employee)
        
        # 검증
        self.assertEqual(self.mock_db.execute_query.call_count, 2)
    
    def test_delete(self):
        """삭제 테스트"""
        # mock 설정 - exists_by_id 호출 시 True 반환하도록 설정
        self.mock_db.execute_query.side_effect = [[{"id": "EMP-001"}], None]  # exists_by_id=True, delete
        
        # 메서드 호출
        self.repo.delete("EMP-001")
        
        # 검증
        self.assertEqual(self.mock_db.execute_query.call_count, 2)
    
    def test_count(self):
        """개수 조회 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [{"count": 10}]
        
        # 메서드 호출
        result = self.repo.count()
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(result, 10)

if __name__ == '__main__':
    unittest.main() 