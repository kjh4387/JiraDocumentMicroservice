from unittest.mock import MagicMock, patch
from app.source.tests.util.test_base import BaseUnitTest
from app.source.application.services.document_service import DocumentService
from app.source.core.exceptions import ValidationError, RenderingError, PdfGenerationError, DocumentAutomationError
import uuid
from datetime import datetime

class TestDocumentService(BaseUnitTest):
    """문서 서비스 단위 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        
        # 각 의존성에 대한 모의 객체 생성
        self.validator_mock = MagicMock()
        self.data_enricher_mock = MagicMock()
        self.renderer_mock = MagicMock()
        self.pdf_generator_mock = MagicMock()
        
        # 테스트 대상 서비스 생성
        self.service = DocumentService(
            validator=self.validator_mock,
            data_enricher=self.data_enricher_mock,
            renderer=self.renderer_mock,
            pdf_generator=self.pdf_generator_mock
        )
        
        # 테스트 데이터
        self.test_document_data = {
            "document_type": "employee_contract",
            "employee_id": "TEST-EMP-001",
            "company_id": "TEST-COMP-001",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31"
        }
    
    def test_create_document_success(self):
        """문서 생성 성공 테스트"""
        # 모의 객체 설정
        self.validator_mock.validate.return_value = (True, None)
        self.data_enricher_mock.enrich.return_value = {
            **self.test_document_data,
            "employee_name": "홍길동",
            "company_name": "테스트 회사"
        }
        self.renderer_mock.render.return_value = "<html><body>테스트 문서</body></html>"
        self.pdf_generator_mock.generate.return_value = b"PDF binary data"
        
        # 메서드 호출
        result = self.service.create_document(self.test_document_data)
        
        # 검증
        self.assertEqual(result["document_type"], "employee_contract")
        self.assertIn("document_id", result)
        self.assertIn("created_at", result)
        self.assertEqual(result["html"], "<html><body>테스트 문서</body></html>")
        self.assertEqual(result["pdf"], b"PDF binary data")
        
        # 각 의존성 메서드 호출 검증
        self.validator_mock.validate.assert_called_once_with(self.test_document_data)
        self.data_enricher_mock.enrich.assert_called_once_with(
            "employee_contract", self.test_document_data
        )
        self.renderer_mock.render.assert_called_once()
        self.pdf_generator_mock.generate.assert_called_once()
    
    def test_create_document_validation_error(self):
        """문서 데이터 검증 실패 테스트"""
        # 모의 객체 설정 - 검증 실패
        self.validator_mock.validate.return_value = (False, "필수 필드 누락: employee_id")
        
        # 메서드 호출 및 예외 검증
        with self.assertRaises(ValidationError) as context:
            self.service.create_document(self.test_document_data)
        
        # 오류 메시지 검증
        self.assertIn("유효하지 않은 문서 데이터", str(context.exception))
        self.assertIn("필수 필드 누락: employee_id", str(context.exception))
        
        # 호출 검증
        self.validator_mock.validate.assert_called_once_with(self.test_document_data)
        self.data_enricher_mock.enrich.assert_not_called()
        self.renderer_mock.render.assert_not_called()
        self.pdf_generator_mock.generate.assert_not_called()
    
    def test_create_document_rendering_error(self):
        """렌더링 실패 테스트"""
        # 모의 객체 설정
        self.validator_mock.validate.return_value = (True, None)
        self.data_enricher_mock.enrich.return_value = {
            **self.test_document_data,
            "employee_name": "홍길동",
            "company_name": "테스트 회사"
        }
        self.renderer_mock.render.side_effect = RenderingError("템플릿 문법 오류")
        
        # 메서드 호출 및 예외 검증
        with self.assertRaises(RenderingError) as context:
            self.service.create_document(self.test_document_data)
        
        # 오류 메시지 검증
        self.assertIn("문서 템플릿 렌더링 실패", str(context.exception))
        
        # 호출 검증
        self.validator_mock.validate.assert_called_once()
        self.data_enricher_mock.enrich.assert_called_once()
        self.renderer_mock.render.assert_called_once()
        self.pdf_generator_mock.generate.assert_not_called()
    
    def test_create_document_pdf_generation_error(self):
        """PDF 생성 실패 테스트"""
        # 모의 객체 설정
        self.validator_mock.validate.return_value = (True, None)
        self.data_enricher_mock.enrich.return_value = {
            **self.test_document_data,
            "employee_name": "홍길동",
            "company_name": "테스트 회사"
        }
        self.renderer_mock.render.return_value = "<html><body>테스트 문서</body></html>"
        self.pdf_generator_mock.generate.side_effect = PdfGenerationError("PDF 생성 중 오류 발생")
        
        # 메서드 호출 및 예외 검증
        with self.assertRaises(PdfGenerationError) as context:
            self.service.create_document(self.test_document_data)
        
        # 호출 검증
        self.validator_mock.validate.assert_called_once()
        self.data_enricher_mock.enrich.assert_called_once()
        self.renderer_mock.render.assert_called_once()
        self.pdf_generator_mock.generate.assert_called_once()
    
    def test_create_document_unexpected_error(self):
        """예상치 못한 오류 처리 테스트"""
        # 모의 객체 설정
        self.validator_mock.validate.return_value = (True, None)
        self.data_enricher_mock.enrich.side_effect = Exception("예상치 못한 오류")
        
        # 메서드 호출 및 예외 검증
        with self.assertRaises(DocumentAutomationError) as context:
            self.service.create_document(self.test_document_data)
        
        # 오류 메시지 검증
        self.assertIn("문서 생성 중 오류 발생", str(context.exception))
        
        # 호출 검증
        self.validator_mock.validate.assert_called_once()
        self.data_enricher_mock.enrich.assert_called_once()
        self.renderer_mock.render.assert_not_called()
        self.pdf_generator_mock.generate.assert_not_called()
    
    def test_save_pdf(self):
        """PDF 저장 테스트"""
        # 테스트 데이터
        pdf_data = b"PDF binary data"
        output_path = f"/tmp/test_document_{uuid.uuid4().hex}.pdf"
        
        # 파일 시스템 접근 모의 처리
        with patch("builtins.open", MagicMock()) as mock_open, \
             patch("os.makedirs") as mock_makedirs:
            
            # 메서드 호출
            result = self.service.save_pdf(pdf_data, output_path)
            
            # 검증
            self.assertEqual(result, output_path)
            
            # os.makedirs 호출 검증
            mock_makedirs.assert_called_once()
            
            # open 호출 검증
            mock_open.assert_called_once_with(output_path, 'wb')
            
            # write 호출 검증
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.write.assert_called_once_with(pdf_data)
    
    def test_save_pdf_error(self):
        """PDF 저장 실패 테스트"""
        # 테스트 데이터
        pdf_data = b"PDF binary data"
        output_path = f"/tmp/test_document_{uuid.uuid4().hex}.pdf"
        
        # 파일 시스템 접근 모의 처리 - 오류 발생
        with patch("builtins.open", MagicMock()) as mock_open, \
             patch("os.makedirs") as mock_makedirs:
            
            # open 호출 시 IOError 발생
            mock_open.side_effect = IOError("파일 쓰기 실패")
            
            # 메서드 호출 및 예외 검증
            with self.assertRaises(IOError) as context:
                self.service.save_pdf(pdf_data, output_path)
            
            # 오류 메시지 검증
            self.assertIn("Failed to save PDF", str(context.exception))
            
            # os.makedirs 호출 검증
            mock_makedirs.assert_called_once()

if __name__ == '__main__':
    import unittest
    unittest.main() 