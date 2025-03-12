import unittest
from app.source.core.domain import Company, Employee, Research, Expert

class TestFixtures(unittest.TestCase):
    """테스트 데이터(Fixture) 생성 테스트"""
    
    def test_create_company(self):
        """회사 객체 생성 테스트"""
        company = Company(
            id="COMP-TEST-001",
            company_name="테스트 주식회사",
            biz_id="123-45-67890",
            rep_name="홍길동",
            address="서울시 강남구",
            biz_type="서비스업",
            biz_item="소프트웨어 개발",
            phone="02-1234-5678",
            rep_stamp=None
        )
        
        self.assertEqual(company.id, "COMP-TEST-001")
        self.assertEqual(company.company_name, "테스트 주식회사")
        self.assertEqual(company.biz_id, "123-45-67890")
    
    def test_create_employee(self):
        """직원 객체 생성 테스트"""
        employee = Employee(
            id="EMP-TEST-001",
            name="홍길동",
            email="hong@example.com",  # 필수 필드로 추가
            department="개발팀",
            position="대리",
            phone="010-1234-5678",
            signature=None,
            stamp=None,
            bank_name="우리은행",
            account_number="1002-123-456789"
        )
        
        self.assertEqual(employee.id, "EMP-TEST-001")
        self.assertEqual(employee.name, "홍길동")
        self.assertEqual(employee.email, "hong@example.com")  # email 필드 검증 추가
    
    def test_create_research(self):
        """연구 과제 객체 생성 테스트"""
        research = Research(
            id="PROJ-TEST-001",
            project_name="테스트 프로젝트",
            project_code="TP-2023-001",  # 필수 필드로 추가
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="김연구",
            project_manager_phone="010-9876-5432"
        )
        
        self.assertEqual(research.id, "PROJ-TEST-001")
        self.assertEqual(research.project_name, "테스트 프로젝트")
        self.assertEqual(research.project_code, "TP-2023-001")  # project_code 필드 검증 추가
        # project_number 필드 검증 제거됨

if __name__ == '__main__':
    unittest.main() 