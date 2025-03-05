from typing import Dict, Any, Optional
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class SchemaRegistry:
    """문서 스키마 레지스트리"""
    
    def __init__(self):
        self.document_configs = {}
    
    def register_document_config(self, document_type: str, config: Dict[str, Any]) -> None:
        """문서 유형별 설정 등록"""
        self.document_configs[document_type] = config
        logger.info(f"Registered document config", document_type=document_type)
    
    def get_document_config(self, document_type: str) -> Dict[str, Any]:
        """문서 유형별 설정 조회"""
        if document_type not in self.document_configs:
            logger.warning(f"Document config not found", document_type=document_type)
            return {"direct_fields": {}, "reference_fields": []}
        
        return self.document_configs[document_type]
    
    def get_all_document_types(self) -> list:
        """모든 문서 유형 조회"""
        return list(self.document_configs.keys()) 