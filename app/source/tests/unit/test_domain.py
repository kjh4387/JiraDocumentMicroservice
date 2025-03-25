import unittest
from datetime import date

from app.source.core.domain import Company, Employee, Research, Expert

class TestDomainModels(unittest.TestCase):
    """도메인 모델 테스트"""
    
    def test_company_creation(self):
        """회사 모델 생성 테스트"""
        company = Company(
            id="COMP-001",
            company_name="테스트 주식회사",
            biz_id="123-45-67890",
            rep_name="김대표",
            address="서울시 강남구",
            biz_type="서비스업",
            biz_item="소프트웨어 개발",
            phone="02-1234-5678"
        )
        
        self.assertEqual(company.id, "COMP-001")
        self.assertEqual(company.company_name, "테스트 주식회사")
        self.assertEqual(company.biz_id, "123-45-67890")
        self.assertEqual(company.rep_name, "김대표")
        self.assertEqual(company.address, "서울시 강남구")
        self.assertEqual(company.biz_type, "서비스업")
    
    def test_employee_creation(self):
        """직원 모델 생성 테스트"""
        employee = Employee(
            id="EMP-001",
            name="홍길동",
            email="hong@example.com",
            department="개발팀",
            position="선임연구원",
            phone="010-1234-5678"
        )
        
        self.assertEqual(employee.id, "EMP-001")
        self.assertEqual(employee.name, "홍길동")
        self.assertEqual(employee.email, "hong@example.com")
        self.assertEqual(employee.department, "개발팀")
        self.assertEqual(employee.position, "선임연구원")
    
    def test_research_creation(self):
        """연구 과제 모델 생성 테스트"""
        research = Research(
            id="PROJ-001",
            project_name="AI 기반 문서 자동화 연구",
            project_code="AI-2023-001",
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="김연구"
        )
        
        self.assertEqual(research.id, "PROJ-001")
        self.assertEqual(research.project_name, "AI 기반 문서 자동화 연구")
        self.assertEqual(research.project_code, "AI-2023-001")
        self.assertEqual(research.project_period, "2023-01-01 ~ 2023-12-31")
        self.assertEqual(research.project_manager, "김연구")
    
    def test_expert_creation(self):
        """전문가 모델 생성 테스트"""
        expert = Expert(
            id="EXP-001",
            name="이전문",
            affiliation="서울대학교",
            position="교수",
            email="expert@example.com"
        )
        
        self.assertEqual(expert.id, "EXP-001")
        self.assertEqual(expert.name, "이전문")
        self.assertEqual(expert.affiliation, "서울대학교")
        self.assertEqual(expert.position, "교수")
        self.assertEqual(expert.email, "expert@example.com")

if __name__ == '__main__':
    unittest.main()
