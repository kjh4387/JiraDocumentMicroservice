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
            account_number="1002-123-456789",
            jira_account_id="712020:9373b1a0-2da9-4202-a103-01402f8fa0e5"  # jira_account_id 필드 추가
        )
        
        self.assertEqual(employee.id, "EMP-TEST-001")
        self.assertEqual(employee.name, "홍길동")
        self.assertEqual(employee.email, "hong@example.com")  # email 필드 검증 추가
        self.assertEqual(employee.jira_account_id, "712020:9373b1a0-2da9-4202-a103-01402f8fa0e5")  # jira_account_id 검증 추가
    
    def test_create_research(self):
        """연구 과제 객체 생성 테스트"""
        research = Research(
            id="PROJ-TEST-001",
            project_name="테스트 프로젝트",
            project_code="TP-2023-001",  # 필수 필드로 추가
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="김연구"
        )
        
        self.assertEqual(research.id, "PROJ-TEST-001")
        self.assertEqual(research.project_name, "테스트 프로젝트")
        self.assertEqual(research.project_code, "TP-2023-001")  # project_code 필드 검증 추가
        # project_number 필드 검증 제거됨
    
    def test_create_expert(self):
        """전문가 객체 생성 테스트"""
        expert = Expert(
            id="EXP-TEST-001",
            name="이전문",
            affiliation="서울대학교",
            position="교수",
            email="expert@example.com",
            phone="010-1111-2222",
            specialty="인공지능"
        )
        
        self.assertEqual(expert.id, "EXP-TEST-001")
        self.assertEqual(expert.name, "이전문")
        self.assertEqual(expert.affiliation, "서울대학교")
        self.assertEqual(expert.position, "교수")
        self.assertEqual(expert.email, "expert@example.com")

if __name__ == '__main__':
    unittest.main() 