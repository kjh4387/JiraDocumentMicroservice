import weasyprint
from weasyprint import CSS
from app.source.core.interfaces import PdfGenerator
from app.source.core.exceptions import PdfGenerationError
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class WeasyPrintPdfGenerator(PdfGenerator):
    """WeasyPrint를 사용한 PDF 생성"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("Initializing WeasyPrintPdfGenerator")
    
    def generate(self, html: str) -> bytes:
        """HTML을 PDF로 변환"""
        self.logger.debug("Generating PDF from HTML (length: %d)", len(html))
        
        try:
            # 스케일링을 위한 CSS 설정
            css_string = """
                @page {
                    size: A4;
                    margin: 1cm;
                }
                html {
                    zoom: 0.75;  /* 내용을 축소하여 페이지에 맞춤 */
                }
                body {
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }
                .A4 {
                    max-width: 100% !important;
                    width: 210mm !important;  /* A4 너비로 강제 조정 */
                    margin: 0 auto !important;
                    padding: 10mm !important;
                    box-sizing: border-box !important;
                }
            """
            
            # CSS 적용하여 PDF 생성
            pdf_bytes = weasyprint.HTML(string=html).write_pdf(
                stylesheets=[CSS(string=css_string)]
            )
            
            self.logger.debug("PDF generated successfully (size: %d bytes)", len(pdf_bytes))
            return pdf_bytes
        except Exception as e:
            self.logger.error("PDF generation failed: %s", str(e))
            raise PdfGenerationError(f"Failed to generate PDF: {str(e)}")
