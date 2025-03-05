import unittest
from unittest.mock import MagicMock, patch
from app.source.application.services.document_service import DocumentService

class TestDocumentService(unittest.TestCase):
    
    def setUp(self):
        # Mock 객체 생성
        self.preprocessor = MagicMock()
        self.document_processor = MagicMock()
        self.repositories = {
            "employee": MagicMock(),
            "company": MagicMock()
        }
        
        # 전처리기 모의 동작 설정
        self.preprocessor.preprocess.return_value = {
            "document_type": "테스트문서",
            "direct_data": {"processed": True}
        }
        
        # 문서 처리기 모의 동작 설정
        self.document_processor.process.return_value = {
            "document_type": "테스트문서",
            "title": "처리된 제목",
            "content": "처리된 내용"
        }
        
        # 문서 서비스 생성
        self.service = DocumentService(
            preprocessors=[self.preprocessor],
            document_processor=self.document_processor,
            repositories=self.repositories
        )
    
    def test_process_document(self):
        # 테스트 요청 데이터
        request = {
            "document_type": "테스트문서",
            "direct_data": {
                "title": "원본 제목",
                "content": "원본 내용"
            }
        }
        
        result = self.service.process_document(request)
        
        # 전처리기가 호출되었는지 확인
        self.preprocessor.preprocess.assert_called_once()
        
        # 문서 처리기가 호출되었는지 확인
        self.document_processor.process.assert_called_once()
        
        # 결과가 올바른지 확인
        self.assertEqual(result["document_type"], "테스트문서")
        self.assertEqual(result["title"], "처리된 제목")
        self.assertEqual(result["content"], "처리된 내용")
    
    @patch("app.source.application.services.document_service.uuid.uuid4")
    @patch("app.source.application.services.document_service.datetime")
    def test_create_document(self, mock_datetime, mock_uuid):
        # UUID와 현재 시간 모의 설정
        mock_uuid.return_value = "test-uuid-1234"
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-15T12:00:00"
        
        # validator 모의 객체 추가
        self.service.validator = MagicMock()
        self.service.validator.validate.return_value = (True, None)
        
        # 문서 렌더러와 PDF 생성기 모의 설정
        self.service.renderer = MagicMock()
        self.service.renderer.render.return_value = "<html>테스트 HTML</html>"
        
        self.service.pdf_generator = MagicMock()
        self.service.pdf_generator.generate.return_value = b"PDF binary data"
        
        # 테스트 데이터
        data = {
            "document_type": "테스트문서",
            "title": "테스트 제목",
            "content": "테스트 내용"
        }
        
        # 출력 경로를 지정하지 않은 경우
        result = self.service.create_document(data)
        
        # 문서 ID, 생성 시간 확인
        self.assertEqual(result["document_id"], "test-uuid-1234")
        self.assertEqual(result["created_at"], "2023-01-15T12:00:00")
        
        # 렌더러와 PDF 생성기가 호출되었는지 확인
        self.service.renderer.render.assert_called_once()
        self.service.pdf_generator.generate.assert_called_once() 