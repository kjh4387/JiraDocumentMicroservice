from fastapi import Depends
from app.source.application.services.document_service import DocumentService
from app.source.core.logging import get_logger

logger = get_logger(__name__)

# 싱글톤으로 사용할 서비스 인스턴스
_document_service = None

def init_dependencies(document_service):
    """의존성 초기화"""
    global _document_service
    _document_service = document_service
    logger.info("Dependencies initialized")

def get_document_service() -> DocumentService:
    """문서 서비스 의존성 주입"""
    if _document_service is None:
        logger.error("Document service not initialized")
        raise RuntimeError("Document service not initialized")
        
    return _document_service 