"""
회사 레포지토리 V2 테스트
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional

from app.source.core.domain import Company
from app.source.core.exceptions import DatabaseError
from app.source.infrastructure.repositories.company_repo_v2 import CompanyRepositoryV2
from app.source.infrastructure.persistence.schema_definition import TableSchema, ColumnDefinition

class TestCompanyRepositoryV2(unittest.TestCase):
    """회사 레포지토리 V2 테스트"""
    
    def setUp(self):
        """테스트 사전 설정"""
        # 모의 DB 연결 객체 생성
        self.mock_db = Mock()
        
        # 모의 로거 생성
        self.mock_logger = Mock()
        
        # 테스트용 스키마 생성
        self.schema = TableSchema(
            table_name="companies",
            columns=[
                ColumnDefinition(name="id", data_type="VARCHAR(50)", primary_key=True),
                ColumnDefinition(name="company_name", data_type="VARCHAR(100)", nullable=False),
                ColumnDefinition(name="biz_id", data_type="VARCHAR(50)", nullable=False),
                ColumnDefinition(name="email", data_type="VARCHAR(100)"),
                ColumnDefinition(name="rep_name", data_type="VARCHAR(100)"),
                ColumnDefinition(name="address", data_type="VARCHAR(200)"),
                ColumnDefinition(name="phone", data_type="VARCHAR(50)")
            ],
            logger=self.mock_logger
        )
        
        # 패치 적용
        self.schema_registry_patch = patch('app.source.infrastructure.persistence.schema_definition.SchemaRegistry.get')
        self.mock_schema_registry = self.schema_registry_patch.start()
        self.mock_schema_registry.return_value = self.schema
        
        # 레포지토리 인스턴스 생성
        self.repo = CompanyRepositoryV2(self.mock_db, logger=self.mock_logger)
        
        # 테스트 샘플 데이터
        self.test_company = Company(
            id="COMP-001",
            company_name="테스트 회사",
            biz_id="123-45-67890",
            email="info@testcompany.com",
            rep_name="홍길동",
            address="서울시 강남구",
            phone="02-1234-5678"
        )
        self.test_row = {
            "id": "COMP-001",
            "company_name": "테스트 회사",
            "biz_id": "123-45-67890",
            "email": "info@testcompany.com",
            "rep_name": "홍길동",
            "address": "서울시 강남구",
            "phone": "02-1234-5678"
        }
        
    def tearDown(self):
        """테스트 후 정리"""
        self.schema_registry_patch.stop()
    
    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.repo.schema, self.schema)
        self.assertEqual(self.repo.db, self.mock_db)
        self.assertEqual(self.repo.entity_class, Company)
    
    def test_find_by_id(self):
        """ID로 검색 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [self.test_row]
        
        # 메서드 호출
        result = self.repo.find_by_id("COMP-001")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(result.id, self.test_company.id)
        self.assertEqual(result.company_name, self.test_company.company_name)
        self.assertEqual(result.address, self.test_company.address)
    
    def test_find_by_id_not_found(self):
        """ID로 검색 - 결과 없음 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = []
        
        # 메서드 호출
        result = self.repo.find_by_id("COMP-999")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertIsNone(result)
    
    def test_find_by_id_db_error(self):
        """ID로 검색 - 데이터베이스 오류 테스트"""
        # mock 설정
        self.mock_db.execute_query.side_effect = Exception("DB Connection Error")
        
        # 메서드 호출 및 예외 검증
        with self.assertRaises(DatabaseError):
            self.repo.find_by_id("COMP-001")
    
    def test_find_by_name(self):
        """회사명으로 검색 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [self.test_row]
        
        # 메서드 호출
        result = self.repo.find_by_name("테스트 회사")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(result.id, self.test_company.id)
        self.assertEqual(result.company_name, self.test_company.company_name)
    
    def test_find_by_name_not_found(self):
        """회사명으로 검색 - 결과 없음 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = []
        
        # 메서드 호출
        result = self.repo.find_by_name("존재하지 않는 회사")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertIsNone(result)
    
    def test_search(self):
        """키워드 검색 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [self.test_row]
        
        # 메서드 호출
        result = self.repo.search("테스트")
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, self.test_company.id)
        self.assertEqual(result[0].company_name, self.test_company.company_name)
    
    def test_save_insert(self):
        """저장 (삽입) 테스트"""
        # mock 설정
        self.mock_db.execute_query.side_effect = [[], None]  # exists_by_id=False, _insert
        
        # 메서드 호출
        self.repo.save(self.test_company)
        
        # 검증
        self.assertEqual(self.mock_db.execute_query.call_count, 2)
    
    def test_save_update(self):
        """저장 (업데이트) 테스트"""
        # mock 설정
        self.mock_db.execute_query.side_effect = [[self.test_row], None]  # exists_by_id=True, _update
        
        # 메서드 호출
        self.repo.save(self.test_company)
        
        # 검증
        self.assertEqual(self.mock_db.execute_query.call_count, 2)
    
    def test_delete(self):
        """삭제 테스트"""
        # mock 설정 - exists_by_id 호출 시 True 반환하도록 설정
        self.mock_db.execute_query.side_effect = [[{"id": "COMP-001"}], None]  # exists_by_id=True, delete
        
        # 메서드 호출
        self.repo.delete("COMP-001")
        
        # 검증
        self.assertEqual(self.mock_db.execute_query.call_count, 2)
    
    def test_count(self):
        """개수 조회 테스트"""
        # mock 설정
        self.mock_db.execute_query.return_value = [{"count": 5}]
        
        # 메서드 호출
        result = self.repo.count()
        
        # 검증
        self.mock_db.execute_query.assert_called_once()
        self.assertEqual(result, 5)

if __name__ == '__main__':
    unittest.main() 