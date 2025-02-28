import unittest
from unittest.mock import MagicMock, patch
from core.domain import Company, Employee, Research, Expert
from application.services.data_enricher import DatabaseDataEnricher
from application.services.document_service import DocumentService
from core.exceptions import ValidationError, RenderingError, PdfGenerationError

class TestDataEnricher(unittest.TestCase):
    """데이터 보강 서비스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.company_repo = MagicMock()
        self.employee_repo = MagicMock()
        self.research_repo = MagicMock()
        self.expert_repo = MagicMock()
        
        self.enricher = DatabaseDataEnricher(
            self.company_repo,
            self.employee_repo,
            self.research_repo,
            self.expert_repo
        )
        
        # 테스트 데이터
        self.test_company = Company(
            id="COMP-001",
            company_name="테스트 주식회사",
            biz_id="123-45-67890",
            rep_name="김대표",
            address="서울시 강남구"
        )
        
        self.test_employee = Employee(
            id="EMP-001",
            name="홍길동",
            department="개발팀",
            position="선임연구원",
            email="hong@example.com"
        )
        
        self.test_research = Research(
            id="PROJ-001",
            project_name="AI 기반 문서 자동화 시스템",
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="김연구"
        )
        
        self.test_expert = Expert(
            id="EXP-001",
            name="이전문",
            affiliation="서울대학교",
            position="교수"
        )
    
    def test_enrich_supplier_info(self):
        """공급자 정보 보강 테스트"""
        # 모의 설정
        self.company_repo.find_by_id.return_value = self.test_company
        
        # 테스트 데이터
        data = {
            "document_type": "견적서",
            "supplier_info": {
                "company_id": "COMP-001"
            }
        }
        
        # 테스트 실행
        result = self.enricher.enrich("견적서", data)
        
        # 검증
        self.assertEqual(result["supplier_info"]["company_name"], "테스트 주식회사")
        self.assertEqual(result["supplier_info"]["biz_id"], "123-45-67890")
        self.assertEqual(result["supplier_info"]["rep_name"], "김대표")
        
        # 저장소 호출 검증
        self.company_repo.find_by_id.assert_called_once_with("COMP-001")
    
    def test_enrich_participants(self):
        """참가자 정보 보강 테스트"""
        # 모의 설정
        self.employee_repo.find_by_id.return_value = self.test_employee
        
        # 테스트 데이터
        data = {
            "document_type": "회의록",
            "participants": [
                {"employee_id": "EMP-001"}
            ]
        }
        
        # 테스트 실행
        result = self.enricher.enrich("회의록", data)
        
        # 검증
        self.assertEqual(result["participants"][0]["name"], "홍길동")
        self.assertEqual(result["participants"][0]["department"], "개발팀")
        self.assertEqual(result["participants"][0]["position"], "선임연구원")
        
        # 저장소 호출 검증
        self.employee_repo.find_by_id.assert_called_once_with("EMP-001")
    
    def test_enrich_research_project(self):
        """연구 과제 정보 보강 테스트"""
        # 모의 설정
        self.research_repo.find_by_id.return_value = self.test_research
        
        # 테스트 데이터
        data = {
            "document_type": "출장신청서",
            "research_project_info": {
                "project_id": "PROJ-001"
            }
        }
        
        # 테스트 실행
        result = self.enricher.enrich("출장신청서", data)
        
        # 검증
        self.assertEqual(result["research_project_info"]["project_name"], "AI 기반 문서 자동화 시스템")
        self.assertEqual(result["research_project_info"]["project_period"], "2023-01-01 ~ 2023-12-31")
        self.assertEqual(result["research_project_info"]["project_manager"], "김연구")
        
        # 저장소 호출 검증
        self.research_repo.find_by_id.assert_called_once_with("PROJ-001")
    
    def test_enrich_expert_info(self):
        """전문가 정보 보강 테스트"""
        # 모의 설정
        self.expert_repo.find_by_id.return_value = self.test_expert
        
        # 테스트 데이터
        data = {
            "document_type": "전문가활용계획서",
            "expert_info": {
                "expert_id": "EXP-001"
            }
        }
        
        # 테스트 실행
        result = self.enricher.enrich("전문가활용계획서", data)
        
        # 검증
        self.assertEqual(result["expert_info"]["name"], "이전문")
        self.assertEqual(result["expert_info"]["affiliation"], "서울대학교")
        self.assertEqual(result["expert_info"]["position"], "교수")
        
        # 저장소 호출 검증
        self.expert_repo.find_by_id.assert_called_once_with("EXP-001")

class TestDocumentService(unittest.TestCase):
    """문서 서비스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.validator = MagicMock()
        self.data_enricher = MagicMock()
        self.renderer = MagicMock()
        self.pdf_generator = MagicMock()
        
        self.service = DocumentService(
            self.validator,
            self.data_enricher,
            self.renderer,
            self.pdf_generator
        )
        
        # 테스트 데이터
        self.test_data = {
            "document_type": "견적서",
            "metadata": {
                "document_number": "EST-2023-001"
            }
        }
        
        self.enriched_data = {
            "document_type": "견적서",
            "metadata": {
                "document_number": "EST-2023-001"
            },
            "supplier_info": {
                "company_name": "테스트 주식회사"
            }
        }
        
        # 모의 설정
        self.validator.validate.return_value = (True, None)
        self.data_enricher.enrich.return_value = self.enriched_data
        self.renderer.render.return_value = "<html>Test HTML</html>"
        self.pdf_generator.generate.return_value = b"PDF_BYTES"
    
    def test_create_document_success(self):
        """문서 생성 성공 테스트"""
        # 테스트 실행
        result = self.service.create_document(self.test_data)
        
        # 검증
        self.assertEqual(result["document_type"], "견적서")
        self.assertEqual(result["html"], "<html>Test HTML</html>")
        self.assertEqual(result["pdf"], b"PDF_BYTES")
        
        # 서비스 호출 검증
        self.validator.validate.assert_called_once_with(self.test_data)
        self.data_enricher.enrich.assert_called_once_with("견적서", self.test_data)
        self.renderer.render.assert_called_once_with("견적서", self.enriched_data)
        self.pdf_generator.generate.assert_called_once_with("<html>Test HTML</html>")
    
    def test_create_document_validation_error(self):
        """문서 생성 검증 오류 테스트"""
        # 모의 설정
        self.validator.validate.return_value = (False, "Invalid data")
        
        # 테스트 실행 및 검증
        with self.assertRaises(ValidationError):
            self.service.create_document(self.test_data)
        
        # 서비스 호출 검증
        self.validator.validate.assert_called_once_with(self.test_data)
        self.data_enricher.enrich.assert_not_called()
        self.renderer.render.assert_not_called()
        self.pdf_generator.generate.assert_not_called()
    
    def test_create_document_rendering_error(self):
        """문서 생성 렌더링 오류 테스트"""
        # 모의 설정
        self.renderer.render.side_effect = RenderingError("Rendering failed")
        
        # 테스트 실행 및 검증
        with self.assertRaises(RenderingError):
            self.service.create_document(self.test_data)
        
        # 서비스 호출 검증
        self.validator.validate.assert_called_once_with(self.test_data)
        self.data_enricher.enrich.assert_called_once_with("견적서", self.test_data)
        self.renderer.render.assert_called_once_with("견적서", self.enriched_data)
        self.pdf_generator.generate.assert_not_called()
    
    def test_create_document_pdf_generation_error(self):
        """문서 생성 PDF 생성 오류 테스트"""
        # 모의 설정
        self.pdf_generator.generate.side_effect = PdfGenerationError("PDF generation failed")
        
        # 테스트 실행 및 검증
        with self.assertRaises(PdfGenerationError):
            self.service.create_document(self.test_data)
        
        # 서비스 호출 검증
        self.validator.validate.assert_called_once_with(self.test_data)
        self.data_enricher.enrich.assert_called_once_with("견적서", self.test_data)
        self.renderer.render.assert_called_once_with("견적서", self.enriched_data)
        self.pdf_generator.generate.assert_called_once_with("<html>Test HTML</html>")
    
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_save_pdf(self, mock_open, mock_makedirs):
        """PDF 저장 테스트"""
        # 테스트 실행
        result = self.service.save_pdf(b"PDF_BYTES", "output/test.pdf")
        
        # 검증
        self.assertEqual(result, "output/test.pdf")
        
        # 함수 호출 검증
        mock_makedirs.assert_called_once_with("output", exist_ok = True)
        mock_open.assert_called_once_with("output/test.pdf", "wb")
        mock_open().write.assert_called_once_with(b"PDF_BYTES")

if __name__ == '__main__':
    unittest.main()
