from typing import Dict, Any
import uuid
from datetime import datetime
from app.source.core.interfaces import DocumentGenerationStrategy, DataEnricher, DocumentRenderer, PdfGenerator, JiraClient
from app.source.core.exceptions import RenderingError, PdfGenerationError, DocumentAutomationError
import logging
import os
import tempfile

class DocumentGenerationStrategy(DocumentGenerationStrategy):
    """기본 문서 생성 전략"""
    
    def __init__(
        self,
        data_enricher: DataEnricher,
        renderer: DocumentRenderer,
        pdf_generator: PdfGenerator,
        logger: logging.Logger
    ):
        self.data_enricher = data_enricher
        self.renderer = renderer
        self.pdf_generator = pdf_generator
        self.logger = logger
    
    def generate_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """기본 문서 생성 프로세스"""
        try:
            # 데이터 보강
            render_data = data
            if self.data_enricher:
                try:
                    enriched_data = self.data_enricher.enrich(data["document_type"], data)
                    if enriched_data:
                        render_data = enriched_data
                except Exception as e:
                    self.logger.error("Data enrichment failed: %s", str(e))
            
            # HTML 렌더링
            html = self.renderer.render(data["document_type"], render_data)
            
            # PDF 생성
            pdf = self.pdf_generator.generate(html)
            
            # 임시 파일 저장
            output_path = os.path.join(
                tempfile.mkdtemp(),
                f"{data['key']}_{data['document_type']}.pdf"
            )
            with open(output_path, "wb") as f:
                f.write(pdf)


            # 결과 반환
            return {
                "document_id": str(uuid.uuid4()),
                "document_type": data["document_type"],
                "created_at": datetime.now().isoformat(),
                "html": html,
                "pdf": pdf
            }
            
        except RenderingError as e:
            self.logger.error("Failed to render document: %s", str(e))
            raise
        except PdfGenerationError as e:
            self.logger.error("Failed to generate PDF: %s", str(e))
            raise
        except Exception as e:
            self.logger.error("Unexpected error: %s", str(e))
            raise DocumentAutomationError(f"문서 생성 중 오류 발생: {str(e)}")

class DownloadDocumentStrategy(DocumentGenerationStrategy):
    """문서를 다운로드 받는 경우의 문서 생성 전략"""
    
    def __init__(
        self,
        data_enricher: DataEnricher,
        renderer: DocumentRenderer,
        pdf_generator: PdfGenerator,
        jira_client: JiraClient,
        logger: logging.Logger
    ):
        self.data_enricher = data_enricher
        self.renderer = renderer
        self.pdf_generator = pdf_generator
        self.jira_client = jira_client
        self.logger = logger
    
    def generate_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.logger.info("Download Document from issue : %s", data["document_type"])
            
            # 이슈에서 문서 다운로드
            downloaded_files = self.jira_client.download_attachments(data["issue_key"])
            
            if not downloaded_files:
                raise DocumentAutomationError("No files found to download")
            
            # 첫 번째 파일 사용 (또는 파일 선택 로직 추가)
            file_path = downloaded_files[0]
            
            return {
                "document_id": str(uuid.uuid4()),
                "document_type": data["document_type"],
                "created_at": datetime.now().isoformat(),
                "file_path": file_path
            }
            
        except Exception as e:
            self.logger.error("Error in Download Document: %s", str(e))
            raise DocumentAutomationError(f"Error occurred in Download Document: {str(e)}")

    def download_document(self, issue_key: str) -> Dict[str, Any]:
        """이슈에서 문서 다운로드"""
        try:
            pass
        except Exception as e:
            self.logger.error("Error in Download Document: %s", str(e))
            raise DocumentAutomationError(f"Error occurred in Download Document: {str(e)}") 