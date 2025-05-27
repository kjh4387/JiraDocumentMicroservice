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
from flask import current_app, has_app_context, request


class DocumentStrategyType(Enum):
    GENERATION = "generation"  # 문서 생성
    DOWNLOAD = "download"     # 문서 다운로드

class DefaultDocumentGenerationStrategy(DocumentGenerationStrategy):
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
    
    def _resolve_base_url(self) -> str | None:
        """PDF 생성 시 사용할 base_url 결정 로직"""
        if has_app_context():
            # HTTP 요청 핸들러 안에서 호출된 경우
            return current_app.static_folder      # file:///… 경로
            # 또는  return request.url_root + 'static/'
        else:
            # CLI 실행 등 Flask 컨텍스트가 없을 때
            return str(self.renderer.static_dir)  # DI로 주입해 둔 절대경로
        
    def generate_document(self, data: Dict[str, Any], path = None, file_name = None) -> Dict[str, Any]:
        """기본 문서 생성 프로세스"""
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
        base_url = self._resolve_base_url()
        pdf = self.pdf_generator.generate(html, base_url=base_url)
        
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
            
from pathlib import Path
import uuid, tempfile, shutil, os
from werkzeug.utils import secure_filename

class PictureAttatchedDocumentStrategy(DefaultDocumentGenerationStrategy):
    """
    * 상위 이슈에서 사진을 받아 PDF에 삽입해야 하는 ‘사진 첨부 증빙’용 전략
    * 이미지 상대경로를 render_data["fields"]["image_url"] 로 주입
    * PDF 생성 후 임시 이미지 파일‧디렉터리 정리
    """

    def __init__(
        self,
        data_enricher: DataEnricher,
        renderer: DocumentRenderer,
        pdf_generator: PdfGenerator,
        jira_client: JiraClient,
        logger: logging.Logger,
    ):
        super().__init__(data_enricher, renderer, pdf_generator, logger)
        self.jira_client = jira_client
        self.strategy_type = DocumentStrategyType.GENERATION  # 부모에도 있지만 명시

    # ------------------------------------------------------------
    # generate_document
    # ------------------------------------------------------------
    def generate_document(
        self,
        data: Dict[str, Any],
        path: str | None = None,
        file_name: str | None = None,
    ) -> Dict[str, Any]:
        # 1) 첨부 사진 다운로드
        try:
            downloaded = self.jira_client.download_attachments(
                data["fields"]["parent"]["key"]
            )
            if not downloaded:
                raise DocumentAutomationError("No attachment found in parent issue.")
            source_img = Path(downloaded[0])
        except Exception as e:
            self.logger.error("Picture download failed: %s", e)
            raise

        # 2) base_dir (= .../static) 결정 & 임시 이미지 복사
        base_dir = Path(self._resolve_base_url())  # DefaultDocumentGenerationStrategy 메서드 재활용
        temp_dir = base_dir / "temp" / "picture_attatched_document"
        temp_dir.mkdir(parents=True, exist_ok=True)

        new_img_name = secure_filename(f"{uuid.uuid4().hex}{source_img.suffix}")
        dest_img_path = temp_dir / new_img_name
        shutil.copy2(source_img, dest_img_path)

        # 3) render_data 준비 & fields.image_url 주입
        render_data = data
        if self.data_enricher:
            try:
                enriched = self.data_enricher.enrich(data["document_type"], data)
                if enriched:
                    render_data = enriched
            except Exception as e:
                self.logger.exception("Data enrichment failed: %s", e)

        fields = render_data.setdefault("fields", {})
        # base_dir 아래 상대경로 — 템플릿에서는 {{ image_url }} 로 접근
        rel_image_path = f"temp/picture_attatched_document/{new_img_name}"
        fields["image_url"] = rel_image_path

        # 4) HTML 렌더링 & PDF 생성
        html = self.renderer.render(data["document_type"], render_data)
        pdf_bytes = self.pdf_generator.generate(html, base_url=str(base_dir))

        # 5) PDF 파일 저장
        if path is None:
            path = tempfile.mkdtemp()
        if file_name is None:
            file_name = f"{data['key']}_{data['document_type']}.pdf"

        output_path = Path(path) / file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        # 6) 임시 이미지 정리
        try:
            dest_img_path.unlink(missing_ok=True)
            if not any(temp_dir.iterdir()):
                temp_dir.rmdir()
        except Exception as e:
            self.logger.warning("Temp image cleanup failed: %s", e)

        # 7) 결과 반환
        return {
            "document_id": uuid.uuid4().hex,
            "document_type": data["document_type"],
            "created_at": datetime.now().isoformat(),
            "full_path": str(output_path),
            "file_path": path,
            "file_name": file_name,
            "strategy_type": self.strategy_type.value,
        }

    
    
        

        
        
    

def download_document(jira_client: JiraClient, issue_key: str, logger: logging.Logger) -> Dict[str, Any]:
    """이슈에서 첨부파일 다운로드"""
    try:
        downloaded_files = jira_client.download_attachments(issue_key)
        return downloaded_files
    except Exception as e:
        logger.error("Error in Download Document: %s", str(e))
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