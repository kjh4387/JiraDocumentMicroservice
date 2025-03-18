from typing import Dict, Any, Optional
import os
import uuid
from datetime import datetime
from app.source.core.interfaces import SchemaValidator, DataEnricher, DocumentRenderer, PdfGenerator
from app.source.core.exceptions import ValidationError, RenderingError, PdfGenerationError
from app.source.core.logging import get_logger

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
        
        try:
            # 데이터 검증 - 이제 템플릿 검증도 포함
            is_valid, error = self.validator.validate(data)
            if not is_valid:
                logger.error("Document data validation failed", error=error)
                raise ValidationError(f"유효하지 않은 문서 데이터: {error}")
            
            # 데이터 보강
            enriched_data = self.data_enricher.enrich(document_type, data)
            logger.debug("Document data enriched")
            
            # HTML 렌더링
            html = self.renderer.render(document_type, enriched_data)
            logger.debug("Document rendered to HTML", html_length=len(html))
            
            # PDF 생성
            pdf = self.pdf_generator.generate(html)
            logger.debug("PDF generated", pdf_size=len(pdf))
            
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
            
        except ValidationError as e:
            # 검증 오류 - 그대로 전파
            raise
            
        except RenderingError as e:
            # 렌더링 오류는 템플릿 문제일 가능성이 큼
            logger.error("Failed to render document template", document_type=document_type, error=str(e))
            raise RenderingError(f"문서 템플릿 렌더링 실패: {str(e)}")
            
        except PdfGenerationError as e:
            # PDF 생성 오류
            logger.error("Failed to generate PDF", document_type=document_type, error=str(e))
            raise
            
        except Exception as e:
            # 기타 예상치 못한 오류
            logger.critical("Unexpected error creating document", 
                          document_type=document_type, error=str(e), exc_info=True)
            raise DocumentAutomationError(f"문서 생성 중 오류 발생: {str(e)}")
    
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
