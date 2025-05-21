from typing import Dict, Any, Optional
import os
import uuid
from datetime import datetime
from app.source.core.interfaces import SchemaValidator, DataEnricher, DocumentRenderer, PdfGenerator
from app.source.core.exceptions import ValidationError, RenderingError, PdfGenerationError
import logging
from app.source.core.exceptions import DocumentAutomationError
from app.source.application.services.preprocessor import JiraPreprocessor
from app.source.application.services.document_strategies.document_strategy_factory import DocumentStrategyFactory

logger = logging.getLogger(__name__)

class DocumentService:
    """문서 생성 및 관리 서비스"""
    
    def __init__(
        self,
        data_enricher: DataEnricher,
        renderer: DocumentRenderer,
        pdf_generator: PdfGenerator,
        document_strategy_factory: DocumentStrategyFactory,
        preprocessor: Optional[JiraPreprocessor] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.data_enricher = data_enricher
        self.renderer = renderer
        self.pdf_generator = pdf_generator
        self.preprocessor = preprocessor or JiraPreprocessor()
        self.logger = logger or logging.getLogger(__name__)
        self.strategy_factory = document_strategy_factory
        self.logger.debug("DocumentService initialized")
    
    def get_document_type(self, data: Dict[str, Any]) -> str:
        """문서 타입 추출"""
        document_type = None
        
        try:
            # 방법 1: fields.issuetype.name
            if 'fields' in data and 'issuetype' in data['fields']:
                issuetype = data['fields']['issuetype']
                if isinstance(issuetype, dict) and 'name' in issuetype:
                    document_type = issuetype['name']
                    self.logger.debug("Found document_type from fields.issuetype.name: %s", document_type)
            
            # 방법 2: document_type 직접 키
            if not document_type and 'document_type' in data:
                document_type = data['document_type']
                self.logger.debug("Found document_type from direct key: %s", document_type)
            
            self.logger.info("Creating document for type: %s", document_type)
            return document_type
        
        except Exception as e:
            self.logger.error("Failed to get document_type: %s", str(e), exc_info=True)
            raise DocumentAutomationError(f"문서 타입 추출 중 오류 발생: {str(e)}")
    
    def create_document(self, data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """문서 생성
        
        Args:
            data: 전처리된 Jira 데이터
            document_type: 문서 타입
        Returns:
            생성된 문서 정보
        """
        try:
            # 데이터 전처리
            if self.preprocessor:
                try:
                    self.logger.debug("Preprocessing data")
                    data = self.preprocessor.preprocess(data)
                    self.logger.debug("Data preprocessed successfully")
                except Exception as e:
                    self.logger.error("Data preprocessing failed: %s", str(e))
            else:
                self.logger.debug("Preprocessor is not set, skipping preprocessing")
                raise DocumentAutomationError("Preprocessor is not set")
            
            # 문서 타입에 맞는 전략 선택
            strategy = self.strategy_factory.get_strategy(document_type)
            
            # 선택된 전략으로 문서 생성
            result = strategy.generate_document(data)
            
            self.logger.info("Document created successfully (ID: %s, type: %s)", 
                           result["document_id"], document_type)
            return result
            
        except Exception as e:
            self.logger.error("Error creating document: %s", str(e), exc_info=True)
            raise DocumentAutomationError(f"문서 생성 중 오류 발생: {str(e)}")
    
    def save_pdf(self, pdf_data: bytes, output_path: str) -> str:
        """PDF 파일 저장
        
        Args:
            pdf_data: PDF 바이트 데이터
            output_path: 저장 경로
            
        Returns:
            저장된 파일 경로
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
            return output_path
        except Exception as e:
            self.logger.error("Failed to save PDF: %s", str(e))
            raise DocumentAutomationError(f"PDF 저장 중 오류 발생: {str(e)}")
