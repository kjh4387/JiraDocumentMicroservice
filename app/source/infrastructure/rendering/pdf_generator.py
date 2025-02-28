import weasyprint
from core.interfaces import PdfGenerator
from core.exceptions import PdfGenerationError
from core.logging import get_logger

logger = get_logger(__name__)

class WeasyPrintPdfGenerator(PdfGenerator):
    """WeasyPrint를 사용한 PDF 생성"""
    
    def __init__(self):
        logger.debug("Initializing WeasyPrintPdfGenerator")
    
    def generate(self, html: str) -> bytes:
        """HTML을 PDF로 변환"""
        logger.debug("Generating PDF from HTML", html_length=len(html))
        
        try:
            pdf_bytes = weasyprint.HTML(string=html).write_pdf()
            logger.debug("PDF generated successfully", pdf_size=len(pdf_bytes))
            return pdf_bytes
        except Exception as e:
            logger.error("PDF generation failed", error=str(e))
            raise PdfGenerationError(f"Failed to generate PDF: {str(e)}")
