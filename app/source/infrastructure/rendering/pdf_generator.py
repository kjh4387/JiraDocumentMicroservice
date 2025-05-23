# pdf_generator.py (또는 기존 WeasyPrintPdfGenerator 정의 파일)

import logging
from pathlib import Path
from typing import Optional, Union

import weasyprint
from weasyprint import CSS

from app.source.core.exceptions import PdfGenerationError
from app.source.core.interfaces import PdfGenerator

logger = logging.getLogger(__name__)


class WeasyPrintPdfGenerator(PdfGenerator):
    """WeasyPrint를 사용한 PDF 생성"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("Initializing WeasyPrintPdfGenerator")

    # ───────────────────────────────────────────────────────────────
    def generate(
        self,
        html: str,
        *,
        base_url: Union[str, Path, None] = None,   # ★ 추가
    ) -> bytes:
        """
        HTML을 PDF로 변환.

        Args:
            html: 이미 렌더링된 HTML 문자열
            base_url: 상대 URL 해석 기준 경로
                      예) current_app.static_folder  또는  "http://localhost:8000/"
        Returns:
            PDF 바이너리
        """
        self.logger.debug(
            "Generating PDF (html length=%d, base_url=%s)",
            len(html),
            base_url,
        )

        css_string = """
        @page { size: A4; margin: 1cm; }
        html { zoom: 0.75; }
        body { width: 100%; height: 100%; margin: 0; padding: 0; }
        .A4 { max-width: 100%!important; width: 210mm!important;
              margin: 0 auto!important; padding: 10mm!important;
              box-sizing: border-box!important; }
        """

        try:
            pdf_bytes = weasyprint.HTML(
                string=html,
                base_url=str(base_url) if base_url else None,   # ★ 핵심
            ).write_pdf(stylesheets=[CSS(string=css_string)])

            self.logger.debug("PDF generated successfully (size=%d)", len(pdf_bytes))
            return pdf_bytes

        except Exception as e:
            self.logger.error("PDF generation failed: %s", e, exc_info=True)
            raise PdfGenerationError(f"Failed to generate PDF: {e}") from e
