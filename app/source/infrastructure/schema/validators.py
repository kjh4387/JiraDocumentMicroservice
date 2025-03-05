import json
import jsonschema
from jsonschema import validate
from typing import Dict, Any, Optional, Tuple
from app.source.core.interfaces import SchemaValidator
from app.source.core.exceptions import ValidationError, SchemaError
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class JsonSchemaValidator(SchemaValidator):
    """JSON 스키마를 사용한 데이터 검증"""
    
    def __init__(self, schema_path: str):
        """스키마 파일 경로로 초기화"""
        logger.debug("Initializing JsonSchemaValidator", schema_path=schema_path)
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                
            # 스키마 참조 경로 수정
            if "$defs" in schema and "allOf" in schema:
                for rule in schema["allOf"]:
                    if "then" in rule and "$ref" in rule["then"]:
                        ref = rule["then"]["$ref"]
                        if ref.startswith("#/definitions/"):
                            # #/definitions/ -> #/$defs/로 변경
                            rule["then"]["$ref"] = ref.replace("#/definitions/", "#/$defs/")
                
                # 내부 참조도 수정
                self._fix_refs_recursively(schema["$defs"])
                
            self.schema = schema
            logger.info("Schema loaded successfully")
        except Exception as e:
            logger.error("Failed to load schema", error=str(e))
            raise SchemaError(f"Failed to load schema: {str(e)}")

    def _fix_refs_recursively(self, obj):
        """객체 내의 모든 $ref 참조를 재귀적으로 수정"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str) and value.startswith("#/definitions/"):
                    obj[key] = value.replace("#/definitions/", "#/$defs/")
                elif isinstance(value, (dict, list)):
                    self._fix_refs_recursively(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    self._fix_refs_recursively(item)

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """데이터가 스키마에 맞는지 검증"""
        logger.debug("Validating data against schema", document_type=data.get("document_type", "unknown"))
        try:
            validate(instance=data, schema=self.schema)
            logger.debug("Data validation successful")
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            logger.warning("Data validation failed", error=str(e))
            return False, str(e)
    
    def validate_document_type(self, document_type: str) -> bool:
        """문서 유형이 유효한지 검증"""
        logger.debug("Validating document type", document_type=document_type)
        valid_types = self.schema.get("properties", {}).get("document_type", {}).get("enum", [])
        is_valid = document_type in valid_types
        
        if is_valid:
            logger.debug("Document type is valid", document_type=document_type)
        else:
            logger.warning("Invalid document type", document_type=document_type, valid_types=valid_types)
        
        return is_valid
