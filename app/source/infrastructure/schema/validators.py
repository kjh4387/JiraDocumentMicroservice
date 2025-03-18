import json
import jsonschema
from jsonschema import validate
from typing import Dict, Any, Optional, Tuple
from app.source.core.interfaces import SchemaValidator
from app.source.core.exceptions import ValidationError, SchemaError
from app.source.core.logging import get_logger
from app.source.config.settings import get_settings
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

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
        """데이터가 스키마에 맞는지 검증하고 템플릿 존재 여부도 확인"""
        # 기존 스키마 검증
        is_valid, error = self._validate_against_schema(data)
        if not is_valid:
            return False, error
        
        # 문서 유형 검증
        document_type = data.get("document_type")
        if not self.validate_document_type(document_type):
            return False, f"지원하지 않는 문서 유형: {document_type}"
        
        # 템플릿 존재 여부 검증
        if not self._check_template_exists(document_type):
            return False, f"'{document_type}' 문서 유형에 대한 템플릿이 없습니다."
        
        return True, None

    def _check_template_exists(self, document_type: str) -> bool:
        """문서 유형에 대한 템플릿이 존재하는지 확인"""
        settings = get_settings()
        template_dir = settings.get("template_dir")
        
        # 템플릿 환경 설정
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # 가능한 템플릿 경로들
        template_paths = [
            f"{document_type}.html",
            f"documents/{document_type}.html",
            self._get_template_name_mapping(document_type)
        ]
        
        # 하나라도 존재하면 True 반환
        for path in template_paths:
            try:
                env.get_template(path)
                return True
            except TemplateNotFound:
                continue
        
        return False

    def _get_template_name_mapping(self, document_type: str) -> str:
        """문서 유형에 대한 영문 템플릿 이름 매핑"""
        mapping = {
            "견적서": "estimate.html",
            "거래명세서": "trading_statement.html",
            "출장신청서": "travel_application.html",
            "출장정산신청서": "travel_expense.html",
            "회의비사용신청서": "meeting_expense.html",
            "회의록": "meeting_minutes.html",
            "구매의뢰서": "purchase_order.html",
            "전문가활용계획서": "expert_util_plan.html",
            "전문가자문확인서": "expert_consult_confirm.html",
            "지출결의서": "expenditure.html"
        }
        return mapping.get(document_type, "unknown.html")

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
