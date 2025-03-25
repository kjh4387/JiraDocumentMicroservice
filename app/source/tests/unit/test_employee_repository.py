from app.source.tests.util.test_base import BaseUnitTest
from app.source.core.domain import Employee
from app.source.infrastructure.repositories.employee_repo import EmployeeRepository
from app.source.core.exceptions import DatabaseError
from datetime import date

class TestEmployeeRepository(BaseUnitTest):
    """직원 저장소 단위 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        
        # 테스트 대상 객체 생성
        self.repo = EmployeeRepository(self.db_mock)
        
        # 테스트용 직원 데이터
        self.test_employee_dict = {
            "id": "TEST-EMP-001",
            "name": "홍길동",
            "email": "test@example.com",
            "department": "개발팀",
            "position": "선임연구원",
            "phone": "010-1234-5678",
            "signature": None,
            "stamp": None,
            "bank_name": "테스트은행",
            "account_number": "123-456-789",
            "birth_date": date(1990, 1, 1),
            "address": "서울시 강남구 테스트로 123",
            "fax": "02-1234-5678",
            "jira_account_id": "712020:9373b1a0-2da9-4202-a103-01402f8fa0e5"
        }
        
        # 픽스처로부터 직원 객체 생성
        self.test_employee = self.fixtures.create_test_employee()
    
    def test_find_by_id_success(self):
        """ID로 직원 조회 성공 테스트"""
        # 모의 DB 응답 설정
        self.set_db_find_result(self.test_employee_dict)
        
        # 메서드 호출
        result = self.repo.find_by_id("TEST-EMP-001")
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "TEST-EMP-001")
        self.assertEqual(result.name, "홍길동")
        self.assertEqual(result.email, "test@example.com")
        
        # 쿼리 호출 검증
        self.assert_query_called_with("SELECT * FROM employees WHERE id = %s", ("TEST-EMP-001",))
    
    def test_find_by_id_not_found(self):
        """존재하지 않는 ID로 직원 조회 테스트"""
        # 모의 DB 응답 설정 - 결과 없음
        self.set_db_find_result()
        
        # 메서드 호출
        result = self.repo.find_by_id("NONEXISTENT-ID")
        
        # 검증
        self.assertIsNone(result)
        
        # 쿼리 호출 검증
        self.assert_query_called_with("SELECT * FROM employees WHERE id = %s", ("NONEXISTENT-ID",))
    
    def test_find_by_email_success(self):
        """이메일로 직원 조회 성공 테스트"""
        # 모의 DB 응답 설정
        self.set_db_find_result(self.test_employee_dict)
        
        # 메서드 호출
        result = self.repo.find_by_email("test@example.com")
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "TEST-EMP-001")
        self.assertEqual(result.name, "홍길동")
        self.assertEqual(result.email, "test@example.com")
        
        # 쿼리 호출 검증
        self.assert_query_called_with("SELECT * FROM employees WHERE email = %s", ("test@example.com",))
    
    def test_find_by_department_success(self):
        """부서로 직원 목록 조회 성공 테스트"""
        # 모의 DB 응답 설정 - 여러 직원 결과
        self.db_mock.set_default_result([
            self.test_employee_dict,
            {
                "id": "TEST-EMP-002",
                "name": "김철수",
                "email": "kim@example.com",
                "department": "개발팀",
                "position": "연구원",
                "phone": "010-2345-6789",
                "signature": None,
                "stamp": None,
                "bank_name": "테스트은행",
                "account_number": "234-567-890",
                "birth_date": date(1992, 2, 2),
                "address": "서울시 강남구 테스트로 456",
                "fax": "02-2345-6789"
            }
        ])
        
        # 메서드 호출
        results = self.repo.find_by_department("개발팀")
        
        # 검증
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, "TEST-EMP-001")
        self.assertEqual(results[1].id, "TEST-EMP-002")
        
        # 쿼리 호출 검증
        self.assert_query_called_with("SELECT * FROM employees WHERE department = %s", ("개발팀",))
    
    def test_find_by_criteria_success(self):
        """조건으로 직원 목록 조회 성공 테스트"""
        # 모의 DB 응답 설정
        self.set_db_find_result(self.test_employee_dict)
        
        # 메서드 호출 - 직위로 조회
        criteria = {"position": "선임연구원"}
        results = self.repo.find_by_criteria(criteria)
        
        # 검증
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "TEST-EMP-001")
        self.assertEqual(results[0].position, "선임연구원")
        
        # 쿼리 호출 검증 (정확한 쿼리 구조 파악이 어려우므로 부분 검증)
        self.assert_query_called_with("SELECT * FROM employees WHERE")
    
    def test_save_new_employee(self):
        """새 직원 저장 테스트"""
        # 모의 DB 응답 설정 - 기존 직원 없음
        self.set_db_find_result()
        
        # 메서드 호출
        result = self.repo.save(self.test_employee)
        
        # 검증
        self.assertEqual(result.id, self.test_employee.id)
        self.assertEqual(result.name, self.test_employee.name)
        
        # 쿼리 호출 검증 - INSERT 쿼리 호출 확인
        self.assert_query_called_with("INSERT INTO employees")
    
    def test_save_update_employee(self):
        """기존 직원 업데이트 테스트"""
        # 모의 DB 응답 설정 - 기존 직원 있음
        original_employee_dict = dict(self.test_employee_dict)
        self.set_db_find_result(original_employee_dict)
        
        # 업데이트할 직원 객체 생성
        updated_employee = Employee(**original_employee_dict)
        updated_employee.position = "수석연구원"  # 직위 변경
        
        # 메서드 호출
        result = self.repo.save(updated_employee)
        
        # 검증
        self.assertEqual(result.id, updated_employee.id)
        self.assertEqual(result.position, "수석연구원")
        
        # 쿼리 호출 검증 - UPDATE 쿼리 호출 확인
        self.assert_query_called_with("UPDATE employees")
    
    def test_delete_success(self):
        """직원 삭제 성공 테스트"""
        # 모의 DB 응답 설정 - 기존 직원 있음
        self.set_db_find_result(self.test_employee_dict)
        
        # 메서드 호출
        result = self.repo.delete("TEST-EMP-001")
        
        # 검증
        self.assertTrue(result)
        
        # 쿼리 호출 검증 - DELETE 쿼리 호출 확인
        self.assert_query_called_with("DELETE FROM employees WHERE id = %s", ("TEST-EMP-001",))
    
    def test_delete_not_found(self):
        """존재하지 않는 직원 삭제 테스트"""
        # 모의 DB 응답 설정 - 직원 없음
        self.set_db_find_result()
        
        # 메서드 호출
        result = self.repo.delete("NONEXISTENT-ID")
        
        # 검증
        self.assertFalse(result)
        
        # DELETE 쿼리가 호출되지 않았는지 확인
        for query_call in self.db_mock.executed_queries:
            if "DELETE FROM employees" in query_call["query"]:
                self.fail("DELETE query was called when employee doesn't exist")

    def test_find_by_jira_account_id_success(self):
        """Jira account ID로 직원 조회 성공 테스트"""
        # 모의 DB 응답 설정
        self.set_db_find_result(self.test_employee_dict)
        
        # 메서드 호출
        result = self.repo.find_by_jira_account_id("712020:9373b1a0-2da9-4202-a103-01402f8fa0e5")
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "TEST-EMP-001")
        self.assertEqual(result.name, "홍길동")
        self.assertEqual(result.jira_account_id, "712020:9373b1a0-2da9-4202-a103-01402f8fa0e5")
        
    def test_find_by_jira_account_id_not_found(self):
        """존재하지 않는 Jira account ID로 직원 조회 테스트"""
        # 모의 DB 응답 설정 - 빈 결과
        self.set_db_find_result([])
        
        # 메서드 호출
        result = self.repo.find_by_jira_account_id("non-existent-id")
        
        # 검증
        self.assertIsNone(result)

if __name__ == '__main__':
    import unittest
    unittest.main() 