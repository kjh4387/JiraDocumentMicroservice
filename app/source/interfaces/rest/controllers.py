from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.source.application.services.document_service import DocumentService
from app.source.core.logging import get_logger
from app.source.interfaces.rest.dependencies import get_document_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/process")
async def process_document(
    request: Dict[str, Any],
    document_service: DocumentService = Depends(get_document_service)
):
    """문서 처리 엔드포인트"""
    try:
        logger.info(f"Processing document request", document_type=request.get("document_type"))
        result = document_service.process_document(request)
        return result
    except Exception as e:
        logger.error(f"Document processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.post("/create")
async def create_document(
    request: Dict[str, Any],
    document_service: DocumentService = Depends(get_document_service)
):
    """문서 생성 엔드포인트"""
    try:
        logger.info(f"Creating document", document_type=request.get("document_type"))
        
        # 1. 문서 처리
        processed_data = document_service.process_document(request)
        
        # 2. 문서 생성 및 PDF 렌더링
        result = document_service.create_document(processed_data)
        
        # 3. 결과 반환
        return {
            "document_id": result["document_id"],
            "document_type": result["document_type"],
            "created_at": result["created_at"]
        }
    except Exception as e:
        logger.error(f"Document creation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Document creation failed: {str(e)}") 