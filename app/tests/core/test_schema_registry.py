import unittest
from app.source.core.schema_registry import SchemaRegistry

class TestSchemaRegistry(unittest.TestCase):
    
    def setUp(self):
        self.registry = SchemaRegistry()
        
        # 테스트용 문서 스키마 등록
        self.test_config = {
            "direct_fields": {
                "title": {"type": "string", "required": True},
                "amount": {"type": "number", "required": True}
            },
            "reference_fields": [
                {
                    "field": "employee_id",
                    "entity_type": "employee",
                    "target_path": "employee_info"
                }
            ]
        }
        self.registry.register_document_config("테스트문서", self.test_config)
    
    def test_register_and_get_config(self):
        # 등록된 설정을 조회
        config = self.registry.get_document_config("테스트문서")
        
        # 설정이 정확히 저장되었는지 확인
        self.assertEqual(config, self.test_config)
        
        # 직접 필드 확인
        self.assertIn("title", config["direct_fields"])
        self.assertEqual(config["direct_fields"]["title"]["type"], "string")
    
    def test_get_nonexistent_config(self):
        # 존재하지 않는 문서 유형에 대한 기본 설정 반환 확인
        config = self.registry.get_document_config("존재하지않는문서")
        
        # 기본 빈 구조가 반환되는지 확인
        self.assertIn("direct_fields", config)
        self.assertIn("reference_fields", config)
        self.assertEqual(len(config["direct_fields"]), 0)
        self.assertEqual(len(config["reference_fields"]), 0)
    
    def test_get_all_document_types(self):
        # 모든 문서 유형 목록 확인
        types = self.registry.get_all_document_types()
        
        # 등록된 문서 유형이 포함되어 있는지 확인
        self.assertIn("테스트문서", types)
        self.assertEqual(len(types), 1) 