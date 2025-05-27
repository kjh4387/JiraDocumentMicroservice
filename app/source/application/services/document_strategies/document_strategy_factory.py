from typing import Dict, Any
from app.source.core.interfaces import DocumentGenerationStrategy, DataEnricher, DocumentRenderer, PdfGenerator, JiraClient
from app.source.application.services.document_strategies.document_strategies import DefaultDocumentGenerationStrategy, DownloadDocumentStrategy, PictureAttatchedDocumentStrategy
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
            "거래명세서",
            "여비규정"
        }

        # 특정 필드 첨부파일 다운로드 후 파일 내에 첨부가 필요한 문서 타입 목록
        self.field_attached_document_types = {
            "출장정산신청서"
        }
        
        # 전략 매핑 초기화
        self._init_strategy_mapping()
    
    def _init_strategy_mapping(self):
        """전략 매핑 초기화"""

        # 1) 파일 자체를 내려받아 재배치-저장하는 유형
        download_map = {
            document_type: (lambda document_type=document_type: DownloadDocumentStrategy(   # ← dt=dt 로 late-binding BUG 예방
                self.data_enricher,
                self.renderer,
                self.pdf_generator,
                self.jira_client,
                self.logger
            ))
            for document_type in self.attatched_document_types
        }

        # 2) 상위 이슈 → 사진 내려받아 PDF 내부에 삽입하는 유형
        picture_map = {
            document_type: (lambda document_type=document_type: PictureAttatchedDocumentStrategy(
                self.data_enricher,
                self.renderer,
                self.pdf_generator,
                self.jira_client,
                self.logger
            ))
            for document_type in self.field_attached_document_types
        }

        # 3) 딕셔너리 병합
        self.strategy_mapping: Dict[str, callable] = {**download_map, **picture_map}

        # 4) 기본(데이터만 받아 PDF 생성) 전략
        self.default_strategy = lambda: DefaultDocumentGenerationStrategy(
            self.data_enricher,
            self.renderer,
            self.pdf_generator,
            self.logger
        )
    
    def get_strategy(self, document_type: str) -> DocumentGenerationStrategy:
        """문서 타입에 맞는 전략 생성
        
        Args:
            document_type: 문서 타입
            
        Returns:
            문서 생성 전략 인스턴스
        """
        strategy_creator = self.strategy_mapping.get(document_type, self.default_strategy)
        strategy = strategy_creator()
        
        self.logger.info(
            "Creating %s strategy for document type: %s",
            strategy.__class__.__name__,
            document_type
        )
        
        return strategy 