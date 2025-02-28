import json
import jsonschema
from jsonschema import validate
from typing import Dict, Any, Optional, Tuple
from core.interfaces import SchemaValidator
from core.exceptions import ValidationError, SchemaError
from core.logging import get_logger

logger = get_logger(__name__)

class JsonSchemaValidator(SchemaValidator):
    """JSON 스키마를 사용한 데이터 검증"""
    
    def __init__(self, schema_path: str):
        logger.debug("Initializing JsonSchemaValidator", schema_path=schema_path)
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            logger.info("Schema loaded successfully", schema_path=schema_path)
        except Exception as e:
            logger.error("Failed to load schema", schema_path=schema_path, error=str(e))
            raise SchemaError(f"Failed to load schema from {schema_path}: {str(e)}")
    
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
