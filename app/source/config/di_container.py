from app.source.core.interfaces import (
    SchemaValidator, DataEnricher, DocumentRenderer, 
    SectionRenderer, PdfGenerator, Repository, UnitOfWork,
    JiraClient, JiraFieldMapper, JiraFieldMappingProvider
)
from app.source.core.domain import Company, Employee, Research, Expert
from app.source.infrastructure.persistence.db_connection import DatabaseConnection, DatabaseUnitOfWork
from app.source.infrastructure.repositories.company_repo import CompanyRepository
from app.source.infrastructure.repositories.employee_repo import EmployeeRepository
from app.source.infrastructure.repositories.research_repo import ResearchRepository
from app.source.infrastructure.repositories.expert_repo import ExpertRepository
from app.source.infrastructure.schema.validators import JsonSchemaValidator
from app.source.infrastructure.rendering.section_renderer import JinjaSectionRenderer
from app.source.infrastructure.rendering.document_renderer import JinjaDocumentRenderer
from app.source.infrastructure.rendering.pdf_generator import WeasyPrintPdfGenerator
from app.source.application.services.data_enricher import DatabaseDataEnricher
from app.source.application.services.document_service import DocumentService
from app.source.application.services.signature_service import SignatureService
from app.source.core.logging import get_logger
from app.source.infrastructure.integrations.jira_client import JiraClient, ApiJiraFieldMappingProvider, FileJiraFieldMappingProvider, JiraFieldMapperimpl

logger = get_logger(__name__)

class DIContainer:
    """의존성 주입 컨테이너"""
    
    def __init__(self, config: dict):
        self.config = config
        logger.debug("DIContainer initialized")
        
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
        self._section_renderer = None
        self._document_renderer = None
        self._pdf_generator = None
        
        # 서비스
        self._data_enricher = None
        self._document_service = None
        self._signature_service = None

        # Jira
        self._jira_client = None
        self._jira_field_mapper = None
        self._jira_field_mapping_provider = None
    
    @property
    def db_connection(self) -> DatabaseConnection:
        """데이터베이스 연결 인스턴스 반환"""
        if self._db_connection is None:
            self._db_connection = DatabaseConnection(self.config["database"])
            logger.debug("DatabaseConnection created")
        return self._db_connection
    
    @property
    def unit_of_work(self) -> UnitOfWork:
        """유닛 오브 워크 인스턴스 반환"""
        if self._unit_of_work is None:
            self._unit_of_work = DatabaseUnitOfWork(self.db_connection)
            logger.debug("UnitOfWork created")
        return self._unit_of_work
    
    @property
    def company_repo(self) -> Repository[Company]:
        """회사 저장소 인스턴스 반환"""
        if self._company_repo is None:
            self._company_repo = CompanyRepository(self.db_connection)
            logger.debug("CompanyRepository created")
        return self._company_repo
    
    @property
    def employee_repo(self) -> Repository[Employee]:
        """직원 저장소 인스턴스 반환"""
        if self._employee_repo is None:
            self._employee_repo = EmployeeRepository(self.db_connection)
            logger.debug("EmployeeRepository created")
        return self._employee_repo
    
    @property
    def research_repo(self) -> Repository[Research]:
        """연구 과제 저장소 인스턴스 반환"""
        if self._research_repo is None:
            self._research_repo = ResearchRepository(self.db_connection)
            logger.debug("ResearchRepository created")
        return self._research_repo
    
    @property
    def expert_repo(self) -> Repository[Expert]:
        """전문가 저장소 인스턴스 반환"""
        if self._expert_repo is None:
            self._expert_repo = ExpertRepository(self.db_connection)
            logger.debug("ExpertRepository created")
        return self._expert_repo
    
    @property
    def schema_validator(self) -> SchemaValidator:
        """스키마 검증 인스턴스 반환"""
        if self._schema_validator is None:
            self._schema_validator = JsonSchemaValidator(self.config["schema_path"])
            logger.debug("SchemaValidator created")
        return self._schema_validator
    
    @property
    def section_renderer(self) -> SectionRenderer:
        """섹션 렌더러 인스턴스 반환"""
        if self._section_renderer is None:
            self._section_renderer = JinjaSectionRenderer(self.config["template_dir"])
            logger.debug("SectionRenderer created")
        return self._section_renderer
    
    @property
    def document_renderer(self) -> DocumentRenderer:
        """문서 렌더러 인스턴스 반환"""
        if self._document_renderer is None:
            self._document_renderer = JinjaDocumentRenderer(
                self.config["template_dir"], 
                self.section_renderer
            )
            logger.debug("DocumentRenderer created")
        return self._document_renderer
    
    @property
    def pdf_generator(self) -> PdfGenerator:
        """PDF 생성기 인스턴스 반환"""
        if self._pdf_generator is None:
            self._pdf_generator = WeasyPrintPdfGenerator()
            logger.debug("PdfGenerator created")
        return self._pdf_generator
    
    @property
    def data_enricher(self) -> DataEnricher:
        """데이터 보강 서비스 인스턴스 반환"""
        if self._data_enricher is None:
            self._data_enricher = DatabaseDataEnricher(
                self.company_repo,
                self.employee_repo,
                self.research_repo,
                self.expert_repo
            )
            logger.debug("DataEnricher created")
        return self._data_enricher
    
    @property
    def signature_service(self) -> SignatureService:
        """서명 서비스 인스턴스 반환"""
        if self._signature_service is None:
            signature_dir = self.config.get("signature_dir", "signatures")
            self._signature_service = SignatureService(
                signature_dir,
                self.employee_repo
            )
            logger.debug("SignatureService created")
        return self._signature_service
    
    @property
    def document_service(self) -> DocumentService:
        """문서 서비스 인스턴스 반환"""
        if self._document_service is None:
            self._document_service = DocumentService(
                self.schema_validator,
                self.data_enricher,
                self.document_renderer,
                self.pdf_generator
            )
            logger.debug("DocumentService created")
        return self._document_service

    @property
    def jira_client(self) -> JiraClient:
        """Jira 클라이언트 인스턴스 반환"""
        if self._jira_client is None:
            jira_config = self.config.get("jira", {})
            self._jira_client = JiraClient(
                jira_base_url=jira_config.get("base_url"),
                username=jira_config.get("username"),
                api_token=jira_config.get("api_token"),
                download_dir=jira_config.get("download_dir")
            )
            logger.debug("JiraClient created")
        return self._jira_client
    
    @property
    def jira_field_mapping_provider(self) -> JiraFieldMappingProvider:
        """Jira 필드 매핑 제공자 인스턴스 반환"""
        if self._jira_field_mapping_provider is None:
            jira_config = self.config.get("jira", {})
            mapping_source = jira_config.get("field_mapping_source", "file")
            
            if mapping_source == "api":
                self._jira_field_mapping_provider = ApiJiraFieldMappingProvider(self.jira_client)
                logger.debug("ApiJiraFieldMappingProvider created")
            else:
                mapping_file = jira_config.get("field_mapping_file")
                self._jira_field_mapping_provider = FileJiraFieldMappingProvider(mapping_file)
                logger.debug("FileJiraFieldMappingProvider created")
        return self._jira_field_mapping_provider
    
    @property
    def jira_field_mapper(self) -> JiraFieldMapper:
        """Jira 필드 매퍼 인스턴스 반환"""
        if self._jira_field_mapper is None:
            self._jira_field_mapper = JiraFieldMapperimpl(self.jira_field_mapping_provider)
            logger.debug("JiraFieldMapperimpl created")
        return self._jira_field_mapper

        
