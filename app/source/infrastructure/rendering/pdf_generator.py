import weasyprint
import os
from app.source.core.interfaces import PdfGenerator
from app.source.core.exceptions import PdfGenerationError
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class WeasyPrintPdfGenerator(PdfGenerator):
    """WeasyPrint를 사용한 PDF 생성"""
    
    def __init__(self):
        logger.debug("Initializing WeasyPrintPdfGenerator")
        # 폰트 설정
        os.environ['WEASYPRINT_FONT_CONFIG'] = '/etc/fonts/fonts.conf'
    
    def generate(self, html: str) -> bytes:
        """HTML을 PDF로 변환"""
        logger.debug("Generating PDF from HTML", html_length=len(html))
        
        try:
            # 명시적 폰트 및 페이지 설정
            pdf_bytes = weasyprint.HTML(string=html).write_pdf(
                stylesheets=[
                    weasyprint.CSS(string="""
                        @font-face {
                            font-family: 'NanumGothic';
                            src: url('/usr/share/fonts/truetype/nanum/NanumGothic.ttf') format('truetype');
                            font-weight: normal;
                            font-style: normal;
                        }
                        
                        @page {
                            size: A4;  /* 210mm x 297mm */
                            margin: 20mm;
                            @top-center {
                                content: '';
                            }
                            @bottom-center {
                                content: '';
                            }
                        }
                        
                        body {
                            font-family: 'NanumGothic', sans-serif;
                            width: 170mm;  /* A4 너비(210mm) - 좌우 여백(40mm) */
                            margin: 0 auto;
                            box-sizing: border-box;
                        }
                        
                        /* 테이블이 너무 넓어지는 것 방지 */
                        table {
                            width: 100%;
                            max-width: 170mm;
                            table-layout: fixed;
                            box-sizing: border-box;
                        }
                        
                        /* 셀 내용이 너무 길면 줄바꿈 */
                        td, th {
                            word-wrap: break-word;
                            overflow-wrap: break-word;
                        }
                    """)
                ]
            )
            logger.debug("PDF generated successfully", pdf_size=len(pdf_bytes))
            return pdf_bytes
        except Exception as e:
            logger.error("PDF generation failed", error=str(e))
            raise PdfGenerationError(f"Failed to generate PDF: {str(e)}")
