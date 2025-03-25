from app.source.tests.util.test_base import BaseIntegrationTest
from app.source.infrastructure.repositories.employee_repo import EmployeeRepository
from datetime import date
import uuid

class TestEmployeeRepositoryIntegration(BaseIntegrationTest):
    """직원 저장소 통합 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        
        # 저장소 객체 생성
        self.repo = self.container.employee_repo
        
        # 테스트 데이터 생성
        self.test_employee = self.fixtures.create_test_employee()
        
        # 테스트에 사용할 고유 아이디
        self.unique_id = f"TEST-EMP-{uuid.uuid4().hex[:8]}"
        self.test_employee.id = self.unique_id
    
    def test_save_and_find_by_id(self):
        """직원 저장 및 ID로 조회 통합 테스트"""
        # 직원 저장
        saved_employee = self.repo.save(self.test_employee)
        
        # 검증
        self.assertEqual(saved_employee.id, self.test_employee.id)
        self.assertEqual(saved_employee.name, self.test_employee.name)
        self.assertEqual(saved_employee.email, self.test_employee.email)
        
        # ID로 조회
        found_employee = self.repo.find_by_id(self.test_employee.id)
        
        # 검증
        self.assertIsNotNone(found_employee)
        self.assertEqual(found_employee.id, self.test_employee.id)
        self.assertEqual(found_employee.name, self.test_employee.name)
        self.assertEqual(found_employee.department, self.test_employee.department)
    
    def test_find_by_email(self):
        """이메일로 직원 조회 통합 테스트"""
        # 고유한 이메일 생성
        unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
        self.test_employee.email = unique_email
        
        # 직원 저장
        self.repo.save(self.test_employee)
        
        # 이메일로 조회
        found_employee = self.repo.find_by_email(unique_email)
        
        # 검증
        self.assertIsNotNone(found_employee)
        self.assertEqual(found_employee.id, self.test_employee.id)
        self.assertEqual(found_employee.email, unique_email)
    
    def test_update_employee(self):
        """직원 정보 업데이트 통합 테스트"""
        # 직원 저장
        self.repo.save(self.test_employee)
        
        # 조회
        employee = self.repo.find_by_id(self.test_employee.id)
        
        # 정보 수정
        employee.position = "수석연구원"
        employee.phone = "010-9876-5432"
        
        # 업데이트
        updated_employee = self.repo.save(employee)
        
        # 검증
        self.assertEqual(updated_employee.position, "수석연구원")
        self.assertEqual(updated_employee.phone, "010-9876-5432")
        
        # 다시 조회해서 확인
        found_employee = self.repo.find_by_id(self.test_employee.id)
        self.assertEqual(found_employee.position, "수석연구원")
        self.assertEqual(found_employee.phone, "010-9876-5432")
    
    def test_find_by_department(self):
        """부서로 직원 목록 조회 통합 테스트"""
        # 고유한 부서명 생성
        unique_dept = f"TEST-DEPT-{uuid.uuid4().hex[:6]}"
        
        # 여러 직원 생성 및 저장
        employee1 = self.fixtures.create_test_employee({"department": unique_dept, "name": "홍길동"})
        employee2 = self.fixtures.create_test_employee({"department": unique_dept, "name": "김철수"})
        employee3 = self.fixtures.create_test_employee({"department": unique_dept, "name": "이영희"})
        
        self.repo.save(employee1)
        self.repo.save(employee2)
        self.repo.save(employee3)
        
        # 부서별 직원 조회
        employees = self.repo.find_by_department(unique_dept)
        
        # 검증
        self.assertEqual(len(employees), 3)
        
        # 결과에 모든 직원이 포함되어 있는지 확인
        employee_ids = [emp.id for emp in employees]
        self.assertIn(employee1.id, employee_ids)
        self.assertIn(employee2.id, employee_ids)
        self.assertIn(employee3.id, employee_ids)
    
    def test_find_by_criteria(self):
        """조건으로 직원 목록 조회 통합 테스트"""
        # 고유한 값 생성
        unique_val = uuid.uuid4().hex[:6]
        unique_position = f"TEST-POS-{unique_val}"
        unique_bank = f"TEST-BANK-{unique_val}"
        
        # 여러 직원 생성 및 저장
        employee1 = self.fixtures.create_test_employee({
            "position": unique_position,
            "bank_name": unique_bank
        })
        employee2 = self.fixtures.create_test_employee({
            "position": unique_position,
            "bank_name": "다른은행"
        })
        employee3 = self.fixtures.create_test_employee({
            "position": "다른직위",
            "bank_name": unique_bank
        })
        
        self.repo.save(employee1)
        self.repo.save(employee2)
        self.repo.save(employee3)
        
        # 조건으로 조회 1: 직위만
        employees_by_position = self.repo.find_by_criteria({"position": unique_position})
        
        # 검증 1
        self.assertEqual(len(employees_by_position), 2)
        position_employee_ids = [emp.id for emp in employees_by_position]
        self.assertIn(employee1.id, position_employee_ids)
        self.assertIn(employee2.id, position_employee_ids)
        
        # 조건으로 조회 2: 은행만
        employees_by_bank = self.repo.find_by_criteria({"bank_name": unique_bank})
        
        # 검증 2
        self.assertEqual(len(employees_by_bank), 2)
        bank_employee_ids = [emp.id for emp in employees_by_bank]
        self.assertIn(employee1.id, bank_employee_ids)
        self.assertIn(employee3.id, bank_employee_ids)
        
        # 조건으로 조회 3: 직위 + 은행
        employees_by_both = self.repo.find_by_criteria({
            "position": unique_position,
            "bank_name": unique_bank
        })
        
        # 검증 3
        self.assertEqual(len(employees_by_both), 1)
        self.assertEqual(employees_by_both[0].id, employee1.id)
    
    def test_delete_employee(self):
        """직원 삭제 통합 테스트"""
        # 직원 저장
        self.repo.save(self.test_employee)
        
        # ID로 조회하여 존재하는지 확인
        employee = self.repo.find_by_id(self.test_employee.id)
        self.assertIsNotNone(employee)
        
        # 삭제
        result = self.repo.delete(self.test_employee.id)
        
        # 검증 - 삭제 성공
        self.assertTrue(result)
        
        # 다시 조회하여 삭제되었는지 확인
        deleted_employee = self.repo.find_by_id(self.test_employee.id)
        self.assertIsNone(deleted_employee)
    
    def test_delete_nonexistent_employee(self):
        """존재하지 않는 직원 삭제 통합 테스트"""
        # 존재하지 않는 ID로 삭제 시도
        non_existent_id = "NONEXISTENT-EMPLOYEE-ID"
        result = self.repo.delete(non_existent_id)
        
        # 검증 - 삭제 실패
        self.assertFalse(result)

if __name__ == '__main__':
    import unittest
    unittest.main() 