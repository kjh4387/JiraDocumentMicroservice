from typing import Dict, Any
from app.source.core.interfaces import DocumentGenerationStrategy, DataEnricher, DocumentRenderer, PdfGenerator, JiraClient
from app.source.application.services.document_strategies.document_strategies import DocumentGenerationStrategy, DownloadDocumentStrategy
import logging

class DocumentStrategyFactory:
    """문서 생성 전략 팩토리"""
    
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
        
        # 첨부 파일 다운로드 후 재배치 필요한 문서 타입 목록
        self.attatched_document_types = {
            "지출증빙",
            "통장사본",
            "견적서",
            "거래명세서"
        
        }
    
    def get_strategy(self, document_type: str) -> DocumentGenerationStrategy:
        """문서 타입에 맞는 전략 생성
        
        Args:
            document_type: 문서 타입
            
        Returns:
            문서 생성 전략 인스턴스
        """
        if document_type in self.attatched_document_types:
            self.logger.info("Creating Download Document strategy for document type: %s", document_type)
            return DownloadDocumentStrategy(
                self.data_enricher,
                self.renderer,
                self.pdf_generator,
                self.jira_client,
                self.logger
            )
        
        self.logger.info("Creating Creation strategy for document type: %s", document_type)
        return DocumentGenerationStrategy(
            self.data_enricher,
            self.renderer,
            self.pdf_generator,
            self.logger
        ) 