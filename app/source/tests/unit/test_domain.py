import unittest
from datetime import date

from core.domain import Company, Employee, Research, Expert, Document, DocumentSection

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
    
    def test_employee_creation(self):
        """직원 모델 생성 테스트"""
        employee = Employee(
            id="EMP-001",
            name="홍길동",
            department="개발팀",
            position="선임연구원",
            email="hong@example.com",
            phone="010-1234-5678"
        )
        
        self.assertEqual(employee.id, "EMP-001")
        self.assertEqual(employee.name, "홍길동")
        self.assertEqual(employee.department, "개발팀")
        self.assertEqual(employee.position, "선임연구원")
    
    def test_research_creation(self):
        """연구 과제 모델 생성 테스트"""
        research = Research(
            id="PROJ-001",
            project_name="AI 기반 문서 자동화 시스템",
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="김연구"
        )
        
        self.assertEqual(research.id, "PROJ-001")
        self.assertEqual(research.project_name, "AI 기반 문서 자동화 시스템")
        self.assertEqual(research.project_period, "2023-01-01 ~ 2023-12-31")
    
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
    
    def test_document_creation(self):
        """문서 모델 생성 테스트"""
        document = Document(
            id="DOC-001",
            document_type="견적서",
            metadata={"document_number": "EST-2023-001"}
        )
        
        section1 = DocumentSection(
            section_type="metadata",
            data={"document_number": "EST-2023-001", "date_issued": "2023-05-15"}
        )
        
        section2 = DocumentSection(
            section_type="supplier_info",
            data={"company_name": "테스트 주식회사", "rep_name": "김대표"}
        )
        
        document.sections.append(section1)
        document.sections.append(section2)
        
        self.assertEqual(document.id, "DOC-001")
        self.assertEqual(document.document_type, "견적서")
        self.assertEqual(len(document.sections), 2)
        self.assertEqual(document.sections[0].section_type, "metadata")
        self.assertEqual(document.sections[1].section_type, "supplier_info")

if __name__ == '__main__':
    unittest.main()
