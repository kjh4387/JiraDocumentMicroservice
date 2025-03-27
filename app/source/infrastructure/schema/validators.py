import json
import jsonschema
from jsonschema import validate
from typing import Dict, Any, Optional, Tuple
from app.source.core.interfaces import SchemaValidator
from app.source.core.exceptions import ValidationError, SchemaError
from app.source.config.settings import get_settings
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import logging

class JsonSchemaValidator(SchemaValidator):
    """JSON 스키마를 사용한 문서 데이터 검증"""
    
    def __init__(self, schema_path: str, logger: logging.Logger = None):
        """
        Args:
            schema_path: JSON 스키마 파일 경로
            logger: 로거 인스턴스
        """
        self.schema_path = schema_path
        self.logger = logger or logging.getLogger(__name__)
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """스키마 파일 로드"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as file:
                schema = json.load(file)
            self.logger.info("Schema loaded successfully", schema_path=self.schema_path)
            return schema
        except Exception as e:
            self.logger.error("Failed to load schema", error=str(e), schema_path=self.schema_path)
            raise SchemaError(f"Failed to load schema from {self.schema_path}: {str(e)}")
    
    def _validate_against_schema(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """JSON 스키마를 사용하여 데이터 구조 검증"""
        try:
            # 문서 유형 확인
            document_type = data.get("document_type")
            if not document_type:
                return False, "document_type 필드가 누락되었습니다."
            
            # 전체 통합 스키마 사용
            schema = self.schema
            
            # 스키마 검증
            try:
                jsonschema.validate(instance=data, schema=schema)
                return True, None
            except jsonschema.exceptions.ValidationError as e:
                # 검증 오류 메시지 생성
                error_path = " -> ".join([str(p) for p in e.path])
                if error_path:
                    error_message = f"필드 '{error_path}'에서 오류: {e.message}"
                else:
                    error_message = f"검증 오류: {e.message}"
                
                self.logger.warning("Schema validation failed", path=error_path, message=e.message)
                return False, error_message
                
        except Exception as e:
            self.logger.error("Unexpected error during schema validation", error=str(e))
            return False, f"스키마 검증 중 오류 발생: {str(e)}"

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
        
        return True, None

    def validate_document_type(self, document_type: str) -> bool:
        """문서 유형이 유효한지 검증"""
        valid_types = [
            "견적서", "거래명세서", "출장신청서", "출장정산신청서", 
            "회의비사용신청서", "회의록", "구매의뢰서", 
            "전문가활용계획서", "전문가자문확인서", "지출결의서"
        ]
        return document_type in valid_types

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
