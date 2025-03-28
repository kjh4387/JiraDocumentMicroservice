from typing import Dict, Any, Optional
import os
import uuid
from datetime import datetime
from app.source.core.interfaces import SchemaValidator, DataEnricher, DocumentRenderer, PdfGenerator
from app.source.core.exceptions import ValidationError, RenderingError, PdfGenerationError
import logging
from app.source.core.exceptions import DocumentAutomationError
from app.source.application.services.preprocessor import JiraPreprocessor

logger = logging.getLogger(__name__)

class DocumentService:
    """문서 생성 및 관리 서비스"""
    
    def __init__(
        self,
        validator: SchemaValidator,
        data_enricher: DataEnricher,
        renderer: DocumentRenderer,
        pdf_generator: PdfGenerator,
        preprocessor: Optional[JiraPreprocessor] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.validator = validator
        self.data_enricher = data_enricher
        self.renderer = renderer
        self.pdf_generator = pdf_generator
        self.preprocessor = preprocessor or JiraPreprocessor()
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("DocumentService initialized")
    
    def create_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 생성
        
        Args:
            data: 전처리된 Jira 데이터
            
        Returns:
            생성된 문서 정보
        """
        # Jira 데이터 구조 로깅
        self.logger.debug("Jira data structure: %s", 
                         {k: type(v).__name__ for k, v in data.items() if k != 'fields'})
        if 'fields' in data:
            self.logger.debug("Fields structure: %s", 
                             {k: type(v).__name__ for k, v in data['fields'].items() if k in ['issuetype', 'summary', 'created']})
            if 'issuetype' in data['fields']:
                self.logger.debug("Issue type: %s", data['fields']['issuetype'])
        
        # 서명 필드 확인 (디버깅)
        if 'fields' in data and 'assignee' in data['fields']:
            assignee = data['fields']['assignee']
            if isinstance(assignee, dict) and 'signature' in assignee:
                self.logger.debug(f"Signature path found: {assignee['signature']}")
            else:
                self.logger.warning("No signature field found in assignee")
        
        # Jira fields에서 document_type 추출 - 여러 방법으로 시도
        document_type = None
        
        # 방법 1: fields.issuetype.name
        if 'fields' in data and 'issuetype' in data['fields']:
            issuetype = data['fields']['issuetype']
            if isinstance(issuetype, dict) and 'name' in issuetype:
                document_type = issuetype['name']
                self.logger.debug("Found document_type from fields.issuetype.name: %s", document_type)
            elif isinstance(issuetype, str):
                document_type = issuetype
                self.logger.debug("Found document_type from fields.issuetype string: %s", document_type)
        
        # 방법 2: document_type 직접 키
        if not document_type and 'document_type' in data:
            document_type = data['document_type']
            self.logger.debug("Found document_type from direct key: %s", document_type)
           
        self.logger.info("Creating document for type: %s", document_type)
        
        try:
            # 원본 데이터에 document_type 추가
            data_copy = data.copy()
            data_copy['document_type'] = document_type
            
            # 원본 데이터 로깅
            self.logger.debug("Original document data: %s", data_copy)
            
            # 데이터 검증 - 스키마 검증은 나중에 필요할 때 다시 활성화
            # is_valid, error = self.validator.validate(data_copy)
            # if not is_valid:
            #     self.logger.error("Document data validation failed: %s", error, exc_info=True)
            #     raise ValidationError(f"유효하지 않은 문서 데이터: {error}")
            
            # 데이터 전처리 - 마크다운 테이블 파싱 등
            if self.preprocessor:
                try:
                    self.logger.debug("Preprocessing data")
                    data_copy = self.preprocessor.preprocess(data_copy)
                    self.logger.debug("Data preprocessed successfully")
                except Exception as e:
                    self.logger.error("Data preprocessing failed: %s", str(e), exc_info=True)
                    # 전처리 실패해도 계속 진행
            
            # 데이터 보강 - 선택적으로 필요한 필드만 보강 (전체 구조를 바꾸지 않음)
            render_data = data_copy
            if self.data_enricher:
                # 필요한 필드만 보강하도록 Enricher 인터페이스 활용
                # 보강된 데이터는 원본 구조를 유지하면서 필요한 필드만 추가/수정됨
                try:
                    enriched_data = self.data_enricher.enrich(document_type, data_copy)
                    if enriched_data:
                        render_data = enriched_data
                        self.logger.debug("Data enriched for specific fields")
                except Exception as e:
                    self.logger.error("Data enrichment failed: %s", str(e), exc_info=True)
                    # 보강 실패해도 계속 진행
            
            # HTML 렌더링 - Jira 데이터 구조 그대로 전달
            self.logger.debug("Rendering document with Jira data structure")
            html = self.renderer.render(document_type, render_data)
            self.logger.debug("Document rendered to HTML (length: %d)", len(html))
            
            # 디버깅용 HTML 저장
            try:
                debug_dir = os.path.join("debug")
                os.makedirs(debug_dir, exist_ok=True)
                debug_html_path = os.path.join(debug_dir, f"debug_{document_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
                with open(debug_html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                self.logger.debug(f"Debug HTML saved to: {debug_html_path}")
            except Exception as e:
                self.logger.warning(f"Failed to save debug HTML: {str(e)}")
            
            # PDF 생성
            pdf = self.pdf_generator.generate(html)
            self.logger.debug("PDF generated (size: %d bytes)", len(pdf))
            
            # 결과 반환
            result = {
                "document_id": str(uuid.uuid4()),
                "document_type": document_type,
                "created_at": datetime.now().isoformat(),
                "html": html,
                "pdf": pdf
            }
            
            self.logger.info("Document created successfully (ID: %s, type: %s)", 
                           result["document_id"], document_type)
            return result
            
        except ValidationError as e:
            # 검증 오류 - 그대로 전파
            self.logger.error("Validation error: %s", str(e), exc_info=True)
            raise
            
        except RenderingError as e:
            # 렌더링 오류는 템플릿 문제일 가능성이 큼
            self.logger.error("Failed to render document template (type: %s): %s", 
                            document_type, str(e), exc_info=True)
            raise RenderingError(f"문서 템플릿 렌더링 실패: {str(e)}")
            
        except PdfGenerationError as e:
            # PDF 생성 오류
            self.logger.error("Failed to generate PDF (type: %s): %s", 
                            document_type, str(e), exc_info=True)
            raise
            
        except Exception as e:
            # 기타 예상치 못한 오류
            self.logger.critical("Unexpected error creating document (type: %s): %s", 
                               document_type, str(e), exc_info=True)
            raise DocumentAutomationError(f"문서 생성 중 오류 발생: {str(e)}")
    
    def save_pdf(self, pdf_data: bytes, output_path: str, overwrite: bool = True) -> str:
        """PDF 파일 저장
        
        Args:
            pdf_data: PDF 파일 바이트 데이터
            output_path: 저장할 파일 경로
            overwrite: 파일이 이미 존재할 경우 덮어쓰기 여부 (기본값: True)
            
        Returns:
            저장된 파일 경로
            
        Raises:
            FileExistsError: 파일이 이미 존재하고 overwrite가 False인 경우
            IOError: 파일 저장 중 오류 발생 시
        """
        self.logger.debug("Saving PDF to file: %s (overwrite: %s)", output_path, overwrite)
        
        # 디렉토리 확인 및 생성
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            self.logger.debug("Created output directory: %s", output_dir)
        
        # 파일 존재 확인
        if not overwrite and os.path.exists(output_path):
            self.logger.warning("File already exists and overwrite is False: %s", output_path)
            raise FileExistsError(f"File already exists: {output_path}")
        
        # PDF 저장
        try:
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
            
            self.logger.info("PDF saved successfully (path: %s, size: %d bytes)", 
                           output_path, len(pdf_data))
            return output_path
        except Exception as e:
            self.logger.error("Failed to save PDF (path: %s): %s", 
                            output_path, str(e), exc_info=True)
            raise IOError(f"Failed to save PDF to {output_path}: {str(e)}")
