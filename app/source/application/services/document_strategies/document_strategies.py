from typing import Dict, Any
import uuid
from datetime import datetime
from app.source.core.interfaces import DocumentGenerationStrategy, DataEnricher, DocumentRenderer, PdfGenerator, JiraClient
from app.source.core.exceptions import RenderingError, PdfGenerationError, DocumentAutomationError
import logging
import os
import tempfile
import shutil
from enum import Enum

class DocumentStrategyType(Enum):
    GENERATION = "generation"  # 문서 생성
    DOWNLOAD = "download"     # 문서 다운로드

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
        self.strategy_type = DocumentStrategyType.GENERATION
    
    def generate_document(self, data: Dict[str, Any], path = None, file_name = None) -> Dict[str, Any]:
        """기본 문서 생성 프로세스"""
        try:
            # 데이터 보강
            render_data = data
            if self.data_enricher:
                self.logger.debug("Data enrichment started")
                try:
                    enriched_data = self.data_enricher.enrich(data["document_type"], data)
                    if enriched_data:
                        render_data = enriched_data
                except Exception as e:
                    self.logger.error("Data enrichment failed: %s", str(e))
            else:
                self.logger.debug("Data enrichment is not set, skipping")
            
            # HTML 렌더링
            html = self.renderer.render(data["document_type"], render_data)
            
            # PDF 생성
            pdf = self.pdf_generator.generate(html)
            
            # 임시 파일 저장
            if path is None and file_name is not None:
                path = tempfile.mkdtemp()
                output_path = os.path.join(
                    path,
                    file_name
                )
                with open(output_path, "wb") as f:
                    f.write(pdf)
            elif file_name is None and path is not None:
                file_name = f"{data['key']}_{data['document_type']}.pdf"
                output_path = os.path.join(
                    path,
                    file_name
                )
                with open(output_path, "wb") as f:
                    f.write(pdf)
            else:
                path = tempfile.mkdtemp()
                file_name = f"{data['key']}_{data['document_type']}.pdf"
                output_path = os.path.join(path, file_name)
                with open(output_path, "wb") as f:
                    f.write(pdf)


            # 결과 반환
            return {
                "document_id": str(uuid.uuid4()),
                "document_type": data["document_type"],
                "created_at": datetime.now().isoformat(),
                "full_path": output_path,
                "file_path": path,
                "file_name": file_name,
                "strategy_type": self.strategy_type.value
            }
            
        except RenderingError as e:
            self.logger.error("Failed to render document: %s", str(e))
            raise
        except PdfGenerationError as e:
            self.logger.error("Failed to generate PDF: %s", str(e))
            raise
        except Exception as e:
            self.logger.error("Unexpected error: %s", str(e))
            raise DocumentAutomationError(f"문서 생성 중 오류 발생: {str(e)}, path: {path}, file_name: {file_name}")

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
        self.strategy_type = DocumentStrategyType.DOWNLOAD
    
    def generate_document(self, data: Dict[str, Any], path = None, file_name = None) -> Dict[str, Any]:
        try:
            self.logger.info("Download Document from issue : %s", data["document_type"])
            
            # 이슈에서 문서 다운로드
            downloaded_files = self.jira_client.download_attachments(data["key"])
            
            if not downloaded_files:
                raise DocumentAutomationError("No files found to download")
            
            # 첫 번째 파일 사용
            original_file_path = downloaded_files[0]
            
            # 원본 파일의 확장자 추출
            _, extension = os.path.splitext(original_file_path)
            
            if path is None and file_name is not None:
                # 임시 파일 경로 생성
                path = tempfile.mkdtemp()
                output_path = os.path.join(path, file_name)
                shutil.copy2(original_file_path, output_path)
            elif file_name is None and path is not None:
                # 임시 파일명 생성 (원본 확장자 사용)
                file_name = f"{data['key']}_{data['document_type']}.{extension.lstrip('.')}"
                output_path = os.path.join(path, file_name)
                shutil.copy2(original_file_path, output_path)
            else:
                path = tempfile.mkdtemp()
                file_name = f"{data['key']}_{data['document_type']}.{extension.lstrip('.')}"
                output_path = os.path.join(path, file_name)
                shutil.copy2(original_file_path, output_path)
            
            return {
                "document_id": str(uuid.uuid4()),
                "document_type": data["document_type"],
                "created_at": datetime.now().isoformat(),
                "full_path": output_path,
                "file_path": path,
                "file_name": file_name,
                "extension": extension.lstrip('.'),
                "strategy_type": self.strategy_type.value
            }
            
        except Exception as e:
            self.logger.error("Error in Download Document: %s", str(e))
            raise DocumentAutomationError(f"Error occurred in Download Document: {str(e)}")

    def download_document(self, issue_key: str) -> Dict[str, Any]:
        """이슈에서 문서 다운로드"""
        try:
            downloaded_files = self.jira_client.download_attachments(issue_key)
            return downloaded_files
        except Exception as e:
            self.logger.error("Error in Download Document: %s", str(e))
            raise DocumentAutomationError(f"Error occurred in Download Document: {str(e)}") 
        

def get_temp_file_path(issue_key: str, document_type: str, extension: str = "pdf") -> str:
    """임시 파일 경로 생성
    
    Args:
        issue_key: 이슈 키
        document_type: 문서 타입
        extension: 파일 확장자 (기본값: "pdf")
        
    Returns:
        str: 임시 파일 경로
    """
    return os.path.join(
        tempfile.mkdtemp(),
        f"{issue_key}_{document_type}.{extension.lstrip('.')}"
    )