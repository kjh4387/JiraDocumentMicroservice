from app.source.core.interfaces import (
    SchemaValidator, DataEnricher, DocumentRenderer, 
    PdfGenerator, Repository, UnitOfWork,
    JiraClient, JiraFieldMapper, JiraFieldMappingProvider
)
from app.source.core.domain import Company, Employee, Research, Expert
from app.source.infrastructure.persistence.db_connection import DatabaseConnection, DatabaseUnitOfWork
from app.source.infrastructure.repositories.company_repo_v2 import CompanyRepositoryV2
from app.source.infrastructure.repositories.employee_repo_v2 import EmployeeRepositoryV2
from app.source.infrastructure.repositories.research_repo_v2 import ResearchRepositoryV2
from app.source.infrastructure.repositories.expert_repo_v2 import ExpertRepositoryV2
from app.source.infrastructure.rendering.document_renderer import JinjaDocumentRenderer
from app.source.infrastructure.rendering.pdf_generator import WeasyPrintPdfGenerator
from app.source.application.services.data_enricher import SelectiveFieldEnricher
from app.source.application.services.document_service import DocumentService
from app.source.application.services.signature_service import SignatureService
from app.source.infrastructure.integrations.jira_client import JiraClient
from app.source.infrastructure.mapping.jira_field_mapper import ApiJiraFieldMappingProvider, FileJiraFieldMappingProvider, JiraFieldMapperimpl
from app.source.infrastructure.mapping.jira_document_mapper import JiraDocumentMapper
from app.source.application.services.preprocessor import JiraPreprocessor
from app.source.application.services.document_strategies.document_strategy_factory import DocumentStrategyFactory
import logging
import os

class DIContainer:
    """의존성 주입 컨테이너"""
    
    def __init__(self, config: dict, logger: logging.Logger = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("DIContainer initialized")
        
        # 데이터베이스 연결
        self._db_connection = None
        
        # 저장소
        self._company_repo = None
        self._employee_repo = None
        self._research_repo = None
        self._expert_repo = None
        
        # 유닛 오브 워크
        self._unit_of_work = None
        
        # 스키마 검증
        self._schema_validator = None
        
        # 렌더링
        self._document_renderer = None
        self._pdf_generator = None
        
        # 서비스
        self._data_enricher = None
        self._document_service = None
        self._signature_service = None

        # Strategy
        self._document_strategy_factory = None

        # Jira
        self._jira_client = None
        self._jira_field_mapper = None
        self._jira_field_mapping_provider = None
        self._jira_document_mapper = None
    
    @property
    def db_connection(self) -> DatabaseConnection:
        """데이터베이스 연결 인스턴스 반환"""
        if self._db_connection is None:
            self._db_connection = DatabaseConnection(self.config["database"])
            self.logger.debug("DatabaseConnection created")
        return self._db_connection
    
    @property
    def unit_of_work(self) -> UnitOfWork:
        """유닛 오브 워크 인스턴스 반환"""
        if self._unit_of_work is None:
            self._unit_of_work = DatabaseUnitOfWork(self.db_connection)
            self.logger.debug("UnitOfWork created")
        return self._unit_of_work
    
    @property
    def company_repo(self) -> Repository[Company]:
        """회사 저장소 인스턴스 반환"""
        if self._company_repo is None:
            self._company_repo = CompanyRepositoryV2(self.db_connection)
            self.logger.debug("CompanyRepository created")
        return self._company_repo
    
    @property
    def employee_repo(self) -> Repository[Employee]:
        """직원 저장소 인스턴스 반환"""
        if self._employee_repo is None:
            self._employee_repo = EmployeeRepositoryV2(self.db_connection, logger=self.logger)
            self.logger.debug("EmployeeRepository created")
        return self._employee_repo
    
    @property
    def research_repo(self) -> Repository[Research]:
        """연구 과제 저장소 인스턴스 반환"""
        if self._research_repo is None:
            self._research_repo = ResearchRepositoryV2(self.db_connection, logger=self.logger)
            self.logger.debug("ResearchRepository created")
        return self._research_repo
    
    @property
    def expert_repo(self) -> Repository[Expert]:
        """전문가 저장소 인스턴스 반환"""
        if self._expert_repo is None:
            self._expert_repo = ExpertRepositoryV2(self.db_connection, logger=self.logger)
            self.logger.debug("ExpertRepository created")
        return self._expert_repo
    
  
    @property
    def document_renderer(self) -> DocumentRenderer:
        """문서 렌더러 인스턴스 반환"""
        if self._document_renderer is None:
            self._document_renderer = JinjaDocumentRenderer(
                self.config["template_dir"],
                logger=self.logger
            )
            self.logger.debug("DocumentRenderer created")
        return self._document_renderer
    
    @property
    def pdf_generator(self) -> PdfGenerator:
        """PDF 생성기 인스턴스 반환"""
        if self._pdf_generator is None:
            self._pdf_generator = WeasyPrintPdfGenerator(self.logger)
        return self._pdf_generator
    
    @property
    def data_enricher(self) -> DataEnricher:
        """데이터 보강 서비스 인스턴스 반환"""
        if self._data_enricher is None:
            self._data_enricher = SelectiveFieldEnricher(
                self.company_repo,
                self.employee_repo,
                self.research_repo,
                self.expert_repo,
                logger=self.logger
            )
            self.logger.debug("SelectiveFieldEnricher created")
        return self._data_enricher
    
    @property
    def signature_service(self) -> SignatureService:
        """서명 서비스 인스턴스 반환"""
        if self._signature_service is None:
            signature_dir = self.config.get("signature_dir", "signatures")
            self._signature_service = SignatureService(
                signature_dir,
                self.employee_repo,
            )
            self.logger.debug("SignatureService created")
        return self._signature_service
    
    @property
    def document_service(self) -> DocumentService:
        """문서 서비스 인스턴스 반환"""
        if self._document_service is None:
            self._document_service = DocumentService(
                #self.schema_validator,
                self.data_enricher,
                self.document_renderer,
                self.pdf_generator,
                self.document_strategy_factory,
                logger=self.logger
            )
            self.logger.debug("DocumentService created")
        return self._document_service
    
    @property
    def document_strategy_factory(self) -> DocumentStrategyFactory:
        """문서 전략 팩토리 인스턴스 반환"""
        if self._document_strategy_factory is None:
            self._document_strategy_factory = DocumentStrategyFactory(
                self.data_enricher,
                self.document_renderer,
                self.pdf_generator,
                self.jira_client,
                self.logger
            )
            self.logger.debug("DocumentStrategyFactory created")
        return self._document_strategy_factory

    @property
    def jira_client(self) -> JiraClient:
        """Jira 클라이언트 인스턴스 반환"""
        if self._jira_client is None:
            self._jira_client = JiraClient(
                jira_base_url=self.config["jira"]["base_url"],
                username=self.config["jira"]["username"],
                api_token=self.config["jira"]["api_token"],
                download_dir=self.config["jira"]["download_dir"],
                field_mapper=self.jira_field_mapper,
                logger=self.logger
            )
            self.logger.debug("JiraClient created")
        return self._jira_client
    
    @property
    def jira_field_mapping_provider(self) -> JiraFieldMappingProvider:
        """Jira 필드 매핑 제공자 인스턴스 반환"""
        if self._jira_field_mapping_provider is None:
            jira_config = self.config.get("jira", {})
            mapping_source = jira_config.get("field_mapping_source", "file")
            
            if mapping_source == "api":
                # JiraClient 인스턴스 생성 (field_mapper 없이)
                jira_client = JiraClient(
                    jira_base_url=jira_config.get("base_url"),
                    username=jira_config.get("username"),
                    api_token=jira_config.get("api_token"),
                    download_dir=jira_config.get("download_dir")
                )
                self._jira_field_mapping_provider = ApiJiraFieldMappingProvider(jira_client)
                self.logger.debug("ApiJiraFieldMappingProvider created")
            else:
                mapping_file = jira_config.get("field_mapping_file")
                self._jira_field_mapping_provider = FileJiraFieldMappingProvider(mapping_file)
                self.logger.debug("FileJiraFieldMappingProvider created")
        return self._jira_field_mapping_provider
    
    @property
    def jira_field_mapper(self) -> JiraFieldMapper:
        """Jira 필드 매퍼 인스턴스 반환"""
        if self._jira_field_mapper is None:
            self._jira_field_mapper = JiraFieldMapperimpl(
                self.jira_field_mapping_provider,
                logger=self.logger
            )
            self.logger.debug("JiraFieldMapper created")
        return self._jira_field_mapper

    @property
    def jira_document_mapper(self) -> JiraDocumentMapper:
        """Jira 문서 매퍼 인스턴스 반환"""
        if self._jira_document_mapper is None:
            self._jira_document_mapper = JiraDocumentMapper(self.logger)
            self.logger.debug("JiraDocumentMapper created")
        return self._jira_document_mapper

    def initialize_jira_client(self):
        """Jira 클라이언트 초기화 완료"""
        if self._jira_client is not None:
            self._jira_client.field_mapper = self.jira_field_mapper
            self.logger.debug("JiraClient field mapper initialized")

    def create_preprocessor(self):
        """전처리기 생성 및 등록"""
        # 스키마 검증기 가져오기 (필요한 경우)
        schema_validator = self.get('schema_validator')
        
        # 인스턴스 생성
        preprocessor = JiraPreprocessor(schema_validator=schema_validator)
        
        # 등록
        self.register('preprocessor', preprocessor)
        return preprocessor

    def register(self, name, component):
        """컴포넌트 등록"""
        self.components[name] = component

    def get(self, name):
        """컴포넌트 조회"""
        return self.components.get(name)

    def create_document_service(self):
        """문서 서비스 생성 및 등록"""
        # 의존성 조회
        validator = self.get('schema_validator')
        data_enricher = self.get('data_enricher')
        renderer = self.get('document_renderer')
        pdf_generator = self.get('pdf_generator')
        preprocessor = self.get('preprocessor')
        
        # 인스턴스 생성
        service = DocumentService(
            validator=validator,
            data_enricher=data_enricher,
            renderer=renderer,
            pdf_generator=pdf_generator,
            preprocessor=preprocessor,
            logger=self.logger
        )
        
        # 등록
        self.register('document_service', service)
        return service

  
    def create_document_renderer(self):
        """문서 렌더러 생성 및 등록"""
        # 템플릿 디렉토리 설정
        template_dir = self.config.get('template_dir', './templates')
        
        # 인스턴스 생성
        renderer = JinjaDocumentRenderer(
            template_dir=template_dir,
            logger=self.logger
        )
        
        # 등록
        self.register('document_renderer', renderer)
        return renderer

    def create_pdf_generator(self):
        """PDF 생성기 생성 및 등록"""
        # 인스턴스 생성
        generator = WeasyPrintPdfGenerator(logger=self.logger)
        
        # 등록
        self.register('pdf_generator', generator)
        return generator

    def create_preprocessor(self):
        """전처리기 생성 및 등록"""
        # 스키마 검증기 가져오기 (필요한 경우)
        schema_validator = self.get('schema_validator')
        
        # 인스턴스 생성
        preprocessor = JiraPreprocessor(schema_validator=schema_validator)
        
        # 등록
        self.register('preprocessor', preprocessor)
        return preprocessor

    def create_data_enricher(self):
        """데이터 보강기 생성 및 등록"""
        # 필요한 저장소 가져오기
        company_repo = self.get('company_repository')
        employee_repo = self.get('employee_repository')
        research_repo = self.get('research_repository')
        expert_repo = self.get('expert_repository')
        
        # 인스턴스 생성
        enricher = SelectiveFieldEnricher(
            company_repo=company_repo,
            employee_repo=employee_repo,
            research_repo=research_repo,
            expert_repo=expert_repo,
            logger=self.logger
        )
        
        # 등록
        self.register('data_enricher', enricher)
        return enricher

def create_container(config=None):
    """DI 컨테이너 생성 및 초기화"""
    container = DIContainer(config)
    
    # 저장소 생성
    container.create_company_repository()
    container.create_employee_repository()
    container.create_research_repository()
    container.create_expert_repository()
    
    # 렌더링 관련 컴포넌트 생성
    container.create_schema_validator()
    container.create_document_renderer()
    container.create_pdf_generator()
    
    # 전처리 및 보강 컴포넌트 생성
    container.create_preprocessor()
    container.create_data_enricher()
    
    # 서비스 생성
    container.create_document_service()
    
    return container

        
