import unittest
from unittest.mock import MagicMock, patch
from core.domain import Company
from infrastructure.repositories.company_repo import CompanyRepository
from core.exceptions import DatabaseError

class TestCompanyRepository(unittest.TestCase):
    """회사 저장소 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.db_connection = MagicMock()
        self.repo = CompanyRepository(self.db_connection)
        
        # 테스트 데이터
        self.test_company = Company(
            id="COMP-001",
            company_name="테스트 주식회사",
            biz_id="123-45-67890",
            rep_name="김대표",
            address="서울시 강남구"
        )
        
        # DB 결과 모의 설정
        self.db_result = {
            "id": "COMP-001",
            "company_name": "테스트 주식회사",
            "biz_id": "123-45-67890",
            "rep_name": "김대표",
            "address": "서울시 강남구",
            "biz_type": "서비스업",
            "biz_item": "소프트웨어 개발",
            "phone": "02-1234-5678",
            "rep_stamp": None
        }
    
    def test_find_by_id_success(self):
        """ID로 회사 조회 성공 테스트"""
        # 모의 설정
        self.db_connection.execute_query.return_value = [self.db_result]
        
        # 테스트 실행
        company = self.repo.find_by_id("COMP-001")
        
        # 검증
        self.assertIsNotNone(company)
        self.assertEqual(company.id, "COMP-001")
        self.assertEqual(company.company_name, "테스트 주식회사")
        self.assertEqual(company.biz_id, "123-45-67890")
        
        # DB 호출 검증
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM companies WHERE id = %s", 
            ("COMP-001",)
        )
    
    def test_find_by_id_not_found(self):
        """ID로 회사 조회 실패 테스트"""
        # 모의 설정
        self.db_connection.execute_query.return_value = []
        
        # 테스트 실행
        company = self.repo.find_by_id("NONEXISTENT")
        
        # 검증
        self.assertIsNone(company)
        
        # DB 호출 검증
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM companies WHERE id = %s", 
            ("NONEXISTENT",)
        )
    
    def test_find_by_name_success(self):
        """이름으로 회사 조회 성공 테스트"""
        # 모의 설정
        self.db_connection.execute_query.return_value = [self.db_result]
        
        # 테스트 실행
        company = self.repo.find_by_name("테스트 주식회사")
        
        # 검증
        self.assertIsNotNone(company)
        self.assertEqual(company.id, "COMP-001")
        self.assertEqual(company.company_name, "테스트 주식회사")
        
        # DB 호출 검증
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM companies WHERE company_name = %s", 
            ("테스트 주식회사",)
        )
    
    def test_save_new_company(self):
        """새 회사 저장 테스트"""
        # 모의 설정
        self.db_connection.execute_query.side_effect = [
            [],  # find_by_id 결과 (없음)
            []   # insert 결과 (빈 리스트)
        ]
        
        # 테스트 실행
        result = self.repo.save(self.test_company)
        
        # 검증
        self.assertEqual(result, self.test_company)
        
        # DB 호출 검증
        self.assertEqual(self.db_connection.execute_query.call_count, 2)
        self.db_connection.execute_query.assert_any_call(
            "SELECT * FROM companies WHERE id = %s", 
            ("COMP-001",)
        )
    
    def test_save_update_company(self):
        """기존 회사 업데이트 테스트"""
        # 모의 설정
        self.db_connection.execute_query.side_effect = [
            [self.db_result],  # find_by_id 결과 (있음)
            []                # update 결과 (빈 리스트)
        ]
        
        # 테스트 실행
        result = self.repo.save(self.test_company)
        
        # 검증
        self.assertEqual(result, self.test_company)
        
        # DB 호출 검증
        self.assertEqual(self.db_connection.execute_query.call_count, 2)
        self.db_connection.execute_query.assert_any_call(
            "SELECT * FROM companies WHERE id = %s", 
            ("COMP-001",)
        )
    
    def test_delete_success(self):
        """회사 삭제 성공 테스트"""
        # 모의 설정
        self.db_connection.execute_query.side_effect = [
            [self.db_result],  # find_by_id 결과 (있음)
            []                # delete 결과 (빈 리스트)
        ]
        
        # 테스트 실행
        result = self.repo.delete("COMP-001")
        
        # 검증
        self.assertTrue(result)
        
        # DB 호출 검증
        self.assertEqual(self.db_connection.execute_query.call_count, 2)
        self.db_connection.execute_query.assert_any_call(
            "SELECT * FROM companies WHERE id = %s", 
            ("COMP-001",)
        )
        self.db_connection.execute_query.assert_any_call(
            "DELETE FROM companies WHERE id = %s", 
            ("COMP-001",)
        )
    
    def test_delete_not_found(self):
        """존재하지 않는 회사 삭제 테스트"""
        # 모의 설정
        self.db_connection.execute_query.return_value = []  # find_by_id 결과 (없음)
        
        # 테스트 실행
        result = self.repo.delete("NONEXISTENT")
        
        # 검증
        self.assertFalse(result)
        
        # DB 호출 검증
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM companies WHERE id = %s", 
            ("NONEXISTENT",)
        )
    
    def test_database_error(self):
        """데이터베이스 오류 테스트"""
        # 모의 설정
        self.db_connection.execute_query.side_effect = Exception("DB Error")
        
        # 테스트 실행 및 검증
        with self.assertRaises(DatabaseError):
            self.repo.find_by_id("COMP-001")

if __name__ == '__main__':
    unittest.main()
