import unittest
from unittest.mock import MagicMock, patch
from app.source.core.domain import Employee
from app.source.infrastructure.repositories.employee_repo import EmployeeRepository
from app.source.core.exceptions import DatabaseError

class TestEmployeeRepository(unittest.TestCase):
    
    def setUp(self):
        # 데이터베이스 연결 모의 객체 생성
        self.db_connection = MagicMock()
        
        # 테스트 대상 저장소 생성
        self.repo = EmployeeRepository(self.db_connection)
        
        # 테스트용 직원 데이터
        self.test_employee = Employee(
            id="EMP-001",
            name="홍길동",
            email="hong@example.com",
            department="개발팀",
            position="대리",
            phone="010-1234-5678",
            signature=None,
            stamp=None,
            bank_name="우리은행",
            account_number="1002-123-456789"
        )
    
    def test_find_by_id(self):
        """ID로 직원 조회 테스트"""
        # Mock 설정
        self.db_connection.execute_query.return_value = [{
            "id": "EMP-001",
            "name": "홍길동",
            "email": "hong@example.com",
            "department": "개발팀",
            "position": "대리",
            "phone": "010-1234-5678",
            "signature": None,
            "stamp": None,
            "bank_name": "우리은행",
            "account_number": "1002-123-456789"
        }]
        
        # 메서드 호출
        result = self.repo.find_by_id("EMP-001")
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "EMP-001")
        self.assertEqual(result.email, "hong@example.com")
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM employees WHERE id = %s", ("EMP-001",)
        )
    
    def test_find_by_email(self):
        """이메일로 직원 조회 테스트 (새로 추가)"""
        # Mock 설정
        self.db_connection.execute_query.return_value = [{
            "id": "EMP-001",
            "name": "홍길동",
            "email": "hong@example.com",
            "department": "개발팀",
            "position": "대리",
            "phone": "010-1234-5678",
            "signature": None,
            "stamp": None,
            "bank_name": "우리은행",
            "account_number": "1002-123-456789"
        }]
        
        # 메서드 호출
        result = self.repo.find_by_email("hong@example.com")
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "EMP-001")
        self.assertEqual(result.email, "hong@example.com")
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM employees WHERE email = %s", ("hong@example.com",)
        )
    
    def test_save(self):
        """직원 정보 저장 테스트"""
        # Mock 설정 - 직원이 존재하지 않는 경우
        self.db_connection.execute_query.side_effect = [
            [],  # find_by_id 호출 결과 (존재하지 않음)
            []   # INSERT 쿼리 결과
        ]
        
        # 저장 메서드 호출
        result = self.repo.save(self.test_employee)
        
        # 검증
        self.assertEqual(result.id, self.test_employee.id)
        self.assertEqual(result.email, self.test_employee.email)
        
        # 두 번째 호출은 INSERT 쿼리
        _, args, _ = self.db_connection.execute_query.mock_calls[1]
        self.assertIn("INSERT INTO", args[0])
        self.assertIn("employees", args[0])
    
    def test_find_by_email_not_found(self):
        """존재하지 않는 이메일로 조회 테스트 (새로 추가)"""
        # Mock 설정 - 결과 없음
        self.db_connection.execute_query.return_value = []
        
        # 조회 메서드 호출
        result = self.repo.find_by_email("notfound@example.com")
        
        # 검증
        self.assertIsNone(result)
        self.db_connection.execute_query.assert_called_once()

if __name__ == '__main__':
    unittest.main() 