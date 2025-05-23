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

    def __init__(self, base_url: str | Path | None = None, logger: Optional[logging.Logger] = None):
        self.base_url = str(base_url) if base_url else None
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("Initializing WeasyPrintPdfGenerator")

    def generate(
        self,
        html: str,
        *,
        base_url: Optional[Union[str, Path]] = None,
    ) -> bytes:
        """HTML → PDF

        Args:
            html: 렌더링된 HTML 문자열
            base_url: 상대 URL 해석 기준 경로 (미지정 시 self.base_url 사용)
        """
        css_string = """
            @page { size: A4; margin: 1cm; }
            html { zoom: .75; }
            body { width: 100%; height: 100%; margin: 0; padding: 0; }
            .A4 {
                max-width: 100%!important;
                width: 210mm!important;
                margin: 0 auto!important;
                padding: 10mm!important;
                box-sizing: border-box!important;
            }
        """  # ← ★ 여기 추가

        try:
            pdf_bytes = (
                weasyprint.HTML(
                    string=html,
                    base_url=str(base_url or self.base_url) or None,
                )
                .write_pdf(stylesheets=[CSS(string=css_string)])
            )
            return pdf_bytes

        except Exception as exc:
            self.logger.error("PDF generation failed: %s", exc, exc_info=True)
            raise PdfGenerationError(f"Failed to generate PDF: {exc}") from exc