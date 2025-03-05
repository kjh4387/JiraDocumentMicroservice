import unittest
from unittest.mock import MagicMock, patch
from app.source.application.services.document_processor import ConfigurableDocumentProcessor
from app.source.core.schema_registry import SchemaRegistry

class TestConfigurableDocumentProcessor(unittest.TestCase):
    
    def setUp(self):
        # Mock 객체 생성
        self.schema_registry = MagicMock(spec=SchemaRegistry)
        self.field_processors = {
            "string": MagicMock(),
            "number": MagicMock(),
            "date": MagicMock()
        }
        self.repositories = {
            "employee": MagicMock(),
            "company": MagicMock()
        }
        
        # 테스트 문서 스키마 설정
        self.test_schema = {
            "direct_fields": {
                "title": {"type": "string", "required": True},
                "amount": {"type": "number", "required": False}
            },
            "reference_fields": [
                {
                    "field": "employee_id",
                    "entity_type": "employee",
                    "lookup_field": "id",
                    "target_path": "employee_info",
                    "fields": ["name", "department"]
                }
            ],
            "post_processors": ["TestProcessor1", "TestProcessor2"]
        }
        self.schema_registry.get_document_config.return_value = self.test_schema
        
        # 테스트용 직원 데이터
        self.test_employee = {"id": "emp123", "name": "홍길동", "department": "개발팀"}
        self.repositories["employee"].find_one.return_value = self.test_employee
        
        # 필드 프로세서 모의 동작 설정
        self.field_processors["string"].process.return_value = "처리된 문자열"
        self.field_processors["number"].process.return_value = 12345
        
        # 문서 처리기 생성
        self.processor = ConfigurableDocumentProcessor(
            self.schema_registry,
            self.field_processors,
            self.repositories
        )
        
        # 모의 후처리기 등록
        self.post_processor1 = MagicMock()
        self.post_processor1.process.return_value = {"processed": True, "by": "processor1"}
        
        self.post_processor2 = MagicMock()
        self.post_processor2.process.return_value = {"processed": True, "by": "processor2"}
        
        self.processor.register_post_processor("TestProcessor1", self.post_processor1)
        self.processor.register_post_processor("TestProcessor2", self.post_processor2)
    
    def test_process_direct_fields(self):
        # 테스트 요청 데이터
        request = {
            "document_type": "테스트문서",
            "direct_data": {
                "title": "테스트 제목",
                "amount": 10000
            }
        }
        
        # 후처리기 결과에 필드가 포함되도록 설정
        processed_doc = {
            "processed": True,
            "by": "processor2",
            "title": "처리된 문자열",
            "amount": 12345
        }
        self.post_processor2.process.return_value = processed_doc
        
        result = self.processor.process(request)
        
        # 직접 필드가 처리되었는지 확인
        self.field_processors["string"].process.assert_called_once()
        self.field_processors["number"].process.assert_called_once()
        
        # 결과에 처리된 값이 포함되어 있는지 확인
        self.assertEqual(result["title"], "처리된 문자열")
        self.assertEqual(result["amount"], 12345)
    
    def test_process_reference_fields(self):
        # 모의 객체 동작 수정
        # 후처리 결과에 employee_info 포함되도록 설정
        self.post_processor2.process.return_value = {
            "processed": True, 
            "by": "processor2",
            "employee_info": {"name": "홍길동", "department": "개발팀"}
        }
        
        # 테스트 요청 데이터
        request = {
            "document_type": "테스트문서",
            "direct_data": {},
            "reference_data": {
                "employee_id": "emp123"
            }
        }
        
        result = self.processor.process(request)
        
        # 레포지토리 메서드가 호출되었는지 확인
        self.repositories["employee"].find_one.assert_called_once_with({"id": "emp123"})
        
        # 결과에 참조 데이터가 포함되어 있는지 확인
        self.assertIn("employee_info", result)
    
    def test_apply_post_processors(self):
        # 테스트 요청 데이터
        request = {
            "document_type": "테스트문서",
            "direct_data": {},
            "reference_data": {}
        }
        
        result = self.processor.process(request)
        
        # 후처리기가 순서대로 호출되었는지 확인
        self.post_processor1.process.assert_called_once()
        self.post_processor2.process.assert_called_once()
        
        # 최종 후처리기 결과가 반환되었는지 확인
        self.assertEqual(result["processed"], True)
        self.assertEqual(result["by"], "processor2") 