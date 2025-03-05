from typing import Dict, Any, List, Optional
import os
import uuid
from datetime import datetime
from app.source.core.interfaces import SchemaValidator, DataEnricher, DocumentRenderer, PdfGenerator, Repository
from app.source.core.exceptions import ValidationError, RenderingError, PdfGenerationError
from app.source.core.logging import get_logger
import copy
import json

logger = get_logger(__name__)

class DocumentService:
    """문서 처리 서비스"""
    
    def __init__(self, 
                 preprocessors: List,
                 document_processor,
                 repositories: Dict[str, Repository]):
        self.preprocessors = preprocessors
        self.document_processor = document_processor
        self.repositories = repositories
    
    def process_document(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """문서 처리 메인 메서드"""
        document_type = request.get("document_type")
        logger.info(f"Processing document", document_type=document_type)
        
        # 1. 전처리 단계
        processed_request = copy.deepcopy(request)
        for preprocessor in self.preprocessors:
            processed_request = preprocessor.preprocess(processed_request)
        
        # 2. 문서 처리
        document_data = self.document_processor.process(processed_request)
        
        # 3. 문서 데이터 반환
        return document_data
    
    def create_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 생성"""
        document_type = data.get("document_type")
        logger.info("Creating document", document_type=document_type)
        
        try:
            # 데이터 검증
            is_valid, error = self.validator.validate(data)
            if not is_valid:
                logger.error("Document validation failed", document_type=document_type, error=error)
                raise ValidationError(f"Document validation failed: {error}")
            
            # 데이터 보강
            enriched_data = self.data_enricher.enrich(document_type, data)
            logger.debug("Document data enriched")
            
            # HTML 렌더링
            try:
                html = self.renderer.render(document_type, enriched_data)
                logger.debug("Document rendered to HTML", html_length=len(html))
            except RenderingError as e:
                logger.error("Document rendering failed", error=str(e))
                raise
            
            # PDF 생성
            try:
                pdf = self.pdf_generator.generate(html)
                logger.debug("PDF generated", pdf_size=len(pdf))
            except PdfGenerationError as e:
                logger.error("PDF generation failed", error=str(e))
                raise
            
            # 결과 반환
            result = {
                "document_id": str(uuid.uuid4()),
                "document_type": document_type,
                "created_at": datetime.now().isoformat(),
                "html": html,
                "pdf": pdf
            }
            
            logger.info("Document created successfully", 
                       document_id=result["document_id"], document_type=document_type)
            return result
        except Exception as e:
            logger.error("Failed to create document", error=str(e))
            raise
    
    def save_pdf(self, pdf_data: bytes, output_path: str) -> str:
        """PDF 파일 저장"""
        logger.debug("Saving PDF to file", output_path=output_path)
        
        # 디렉토리 확인 및 생성
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            logger.debug("Created output directory", directory=output_dir)
        
        # PDF 저장
        try:
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
            
            logger.info("PDF saved successfully", output_path=output_path, size=len(pdf_data))
            return output_path
        except Exception as e:
            logger.error("Failed to save PDF", output_path=output_path, error=str(e))
            raise IOError(f"Failed to save PDF to {output_path}: {str(e)}")
