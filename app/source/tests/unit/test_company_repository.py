import unittest
from unittest.mock import MagicMock, patch
from app.source.core.domain import Company
from app.source.infrastructure.repositories.company_repo import CompanyRepository
from app.source.core.exceptions import DatabaseError

class TestCompanyRepository(unittest.TestCase):
    
    def setUp(self):
        # 데이터베이스 연결 모의 객체 생성
        self.db_connection = MagicMock()
        
        # 테스트 대상 저장소 생성
        self.repo = CompanyRepository(self.db_connection)
        
        # 테스트용 회사 데이터
        self.test_company = Company(
            id="COMP-001",
            company_name="테스트 회사",
            biz_id="123-45-67890",
            rep_name="홍길동",
            address="서울시 강남구",
            biz_type="서비스업",
            biz_item="소프트웨어 개발",
            phone="02-1234-5678",
            rep_stamp=None
        )
    
    def test_find_by_id(self):
        """ID로 회사 조회 테스트"""
        # Mock 설정
        self.db_connection.execute_query.return_value = [{
            "id": "COMP-001",
            "company_name": "테스트 회사",
            "biz_id": "123-45-67890",
            "rep_name": "홍길동",
            "address": "서울시 강남구",
            "biz_type": "서비스업",
            "biz_item": "소프트웨어 개발",
            "phone": "02-1234-5678",
            "rep_stamp": None
        }]
        
        # 메서드 호출
        result = self.repo.find_by_id("COMP-001")
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "COMP-001")
        self.assertEqual(result.company_name, "테스트 회사")
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM companies WHERE id = %s", ("COMP-001",)
        )
    
    def test_find_by_name(self):
        """회사명으로 회사 조회 테스트 (새로 추가)"""
        # Mock 설정
        self.db_connection.execute_query.return_value = [{
            "id": "COMP-001",
            "company_name": "테스트 회사",
            "biz_id": "123-45-67890",
            "rep_name": "홍길동",
            "address": "서울시 강남구",
            "biz_type": "서비스업",
            "biz_item": "소프트웨어 개발",
            "phone": "02-1234-5678",
            "rep_stamp": None
        }]
        
        # 메서드 호출
        result = self.repo.find_by_name("테스트 회사")
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "COMP-001")
        self.assertEqual(result.company_name, "테스트 회사")
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM companies WHERE company_name = %s", ("테스트 회사",)
        )
    
    def test_save(self):
        """회사 정보 저장 테스트"""
        # Mock 설정 - 회사가 존재하지 않는 경우
        self.db_connection.execute_query.side_effect = [
            [],  # find_by_id 호출 결과 (존재하지 않음)
            []   # INSERT 쿼리 결과
        ]
        
        # 저장 메서드 호출
        result = self.repo.save(self.test_company)
        
        # 검증
        self.assertEqual(result.id, self.test_company.id)
        self.assertEqual(result.company_name, self.test_company.company_name)
        
        # 두 번째 호출은 INSERT 쿼리
        _, args, _ = self.db_connection.execute_query.mock_calls[1]
        self.assertIn("INSERT INTO", args[0])
        self.assertIn("companies", args[0])
    
    def test_find_by_name_not_found(self):
        """존재하지 않는 회사명으로 조회 테스트 (새로 추가)"""
        # Mock 설정 - 결과 없음
        self.db_connection.execute_query.return_value = []
        
        # 조회 메서드 호출
        result = self.repo.find_by_name("존재하지 않는 회사")
        
        # 검증
        self.assertIsNone(result)
        self.db_connection.execute_query.assert_called_once()

if __name__ == '__main__':
    unittest.main() 