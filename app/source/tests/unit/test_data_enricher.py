import unittest
from unittest.mock import MagicMock, patch
from app.source.core.domain import Company, Employee, Research, Expert
from app.source.application.services.data_enricher import DatabaseDataEnricher

class TestDataEnricher(unittest.TestCase):
    
    def setUp(self):
        # Mock 저장소 생성
        self.company_repo = MagicMock()
        self.employee_repo = MagicMock()
        self.research_repo = MagicMock()
        self.expert_repo = MagicMock()
        
        # 테스트 대상 객체 생성
        self.enricher = DatabaseDataEnricher(
            self.company_repo,
            self.employee_repo,
            self.research_repo,
            self.expert_repo
        )
        
        # 테스트용 데이터 설정
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
        
        self.test_research = Research(
            id="PROJ-001",
            project_name="AI 기반 문서 자동화 연구",
            project_code="AI-2023-001",
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="김연구",
            project_manager_phone="010-9876-5432"
        )
    
    def test_enrich_supplier_info_by_id(self):
        """회사 ID로 공급자 정보 보강 테스트"""
        # Mock 설정
        self.company_repo.find_by_id.return_value = self.test_company
        
        # 테스트 데이터
        data = {
            "document_type": "견적서",
            "supplier_info": {
                "company_id": "COMP-001"
            }
        }
        
        # 메서드 호출
        enriched_data = self.enricher.enrich("견적서", data)
        
        # 검증
        self.assertEqual(enriched_data["supplier_info"]["company_name"], "테스트 회사")
        self.assertEqual(enriched_data["supplier_info"]["biz_id"], "123-45-67890")
        self.company_repo.find_by_id.assert_called_once_with("COMP-001")
    
    def test_enrich_supplier_info_by_name(self):
        """회사명으로 공급자 정보 보강 테스트 (새로 추가)"""
        # Mock 설정
        self.company_repo.find_by_name.return_value = self.test_company
        
        # 테스트 데이터
        data = {
            "document_type": "견적서",
            "supplier_info": {
                "company_name": "테스트 회사"
            }
        }
        
        # 메서드 호출
        enriched_data = self.enricher.enrich("견적서", data)
        
        # 검증
        self.assertEqual(enriched_data["supplier_info"]["company_id"], "COMP-001")
        self.assertEqual(enriched_data["supplier_info"]["biz_id"], "123-45-67890")
        self.company_repo.find_by_name.assert_called_once_with("테스트 회사")
    
    def test_enrich_participants_by_email(self):
        """이메일로 참가자 정보 보강 테스트 (새로 추가)"""
        # Mock 설정
        self.employee_repo.find_by_email.return_value = self.test_employee
        
        # 테스트 데이터
        data = {
            "document_type": "회의록",
            "participants": [
                {
                    "email": "hong@example.com"
                }
            ]
        }
        
        # 메서드 호출
        enriched_data = self.enricher.enrich("회의록", data)
        
        # 검증
        self.assertEqual(enriched_data["participants"][0]["employee_id"], "EMP-001")
        self.assertEqual(enriched_data["participants"][0]["name"], "홍길동")
        self.employee_repo.find_by_email.assert_called_once_with("hong@example.com")
    
    def test_enrich_research_project_by_code(self):
        """프로젝트 코드로 연구 과제 정보 보강 테스트 (새로 추가)"""
        # Mock 설정
        self.research_repo.find_by_project_code.return_value = self.test_research
        
        # 테스트 데이터
        data = {
            "document_type": "출장신청서",
            "research_project_info": {
                "project_code": "AI-2023-001"
            }
        }
        
        # 메서드 호출
        enriched_data = self.enricher.enrich("출장신청서", data)
        
        # 검증
        self.assertEqual(enriched_data["research_project_info"]["project_id"], "PROJ-001")
        self.assertEqual(enriched_data["research_project_info"]["project_name"], "AI 기반 문서 자동화 연구")
        self.research_repo.find_by_project_code.assert_called_once_with("AI-2023-001")
    
    def test_enrich_approval_list_by_email(self):
        """이메일로 결재자 정보 보강 테스트 (새로 추가)"""
        # Mock 설정
        self.employee_repo.find_by_email.return_value = self.test_employee
        
        # 테스트 데이터
        data = {
            "document_type": "출장신청서",
            "approval_list": [
                {
                    "email": "hong@example.com"
                }
            ]
        }
        
        # 메서드 호출
        enriched_data = self.enricher.enrich("출장신청서", data)
        
        # 검증
        self.assertEqual(enriched_data["approval_list"][0]["employee_id"], "EMP-001")
        self.assertEqual(enriched_data["approval_list"][0]["name"], "홍길동")
        self.assertEqual(enriched_data["approval_list"][0]["position"], "대리")
        self.employee_repo.find_by_email.assert_called_once_with("hong@example.com")

if __name__ == '__main__':
    unittest.main() 