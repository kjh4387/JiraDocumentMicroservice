from typing import Dict, Any, Optional
import os
import uuid
from datetime import datetime
from core.interfaces import SchemaValidator, DataEnricher, DocumentRenderer, PdfGenerator
from core.exceptions import ValidationError, RenderingError, PdfGenerationError
from core.logging import get_logger

logger = get_logger(__name__)

class DocumentService:
    """문서 생성 및 관리 서비스"""
    
    def __init__(
        self,
        validator: SchemaValidator,
        data_enricher: DataEnricher,
        renderer: DocumentRenderer,
        pdf_generator: PdfGenerator
    ):
        self.validator = validator
        self.data_enricher = data_enricher
        self.renderer = renderer
        self.pdf_generator = pdf_generator
        logger.debug("DocumentService initialized")
    
    def create_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 생성"""
        document_type = data.get("document_type")
        logger.info("Creating document", document_type=document_type)
        
        # 데이터 검증
        is_valid, error = self.validator.validate(data)
        if not is_valid:
            logger.error("Document data validation failed", error=error)
            raise ValidationError(f"Invalid document data: {error}")
        
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
