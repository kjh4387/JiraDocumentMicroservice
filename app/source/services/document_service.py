import os,sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from repository.research_repository import ResearchRepository
from repository.employee_repository import EmployeeRepository
from repository.company_repository import CompanyRepository
from .template_renderer import TemplateRenderer
from pydantic import BaseModel
import logging
from mappers.mapper_impl import *
from mappers.mapper_interfaces import *

class DocumentRequest(BaseModel):
    template_name: str
    published_date: str
    class Config:
        extra = 'allow'

class DocumentService:
    def __init__(
        self, 
        research_repo: ResearchRepository, 
        research_mapper: ResearchContextMapper,
        employee_repo: EmployeeRepository,
        employee_mapper: ResearchContextMapper,
        company_repo: CompanyRepository,
        company_mapper: ResearchContextMapper,


        template_dir: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "template"),
        logger:logging.Logger = None
    ):
        """
        Args:
            research_repo (ResearchRepository): 연구 정보 Repository
            research_mapper (ResearchContextMapper): 연구 정보 Mapper
            employee_repo (EmployeeRepository): 직원 정보 Repository
            employee_mapper (EmployeeContextMapper): 직원 정보 Mapper
            company_repo (CompanyRepository): 회사 정보 Repository
            company_mapper (CompanyContextMapper): 회사 정보 Mapper
            template_dir (str): 템플릿 파일이 저장된 디렉터리 경로
            logger (logging.Logger): Logger 인스턴스
        
        """
        self.research_repo = research_repo
        self.research_mapper = research_mapper
        self.employee_repo = employee_repo
        self.employee_mapper = employee_mapper
        self.company_repo = company_repo
        self.company_mapper = company_mapper
        self.template_renderer = TemplateRenderer()
        self.logger = logger
        self.template_dir = template_dir


    def load_template(self, template_name: str) -> str:
        template_path = os.path.join(self.template_dir, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        with open(template_path, 'r', encoding='utf-8-sig') as file:
            return file.read()
        

    def create_document(self, doc_request: DocumentRequest) -> str:
        doc_data = doc_request.model_dump()

        # DB 조회: 연구 정보
        research_key = doc_data.pop("research_key", None)
        research = self.research_repo.get_by_key(research_key)
        research_context = self.research_mapper.to_context(research)
        
        # DB 조회: 각 참가자 정보 (리스트 순회)
        participants_emails = doc_data.pop("participants",[], None)
        participants_context = []
        for email in doc_request.participants:
            employee = self.employee_repo.get_by_email(email)
            participants_context.append(self.employee_mapper.to_context(employee))

        
        
        # 템플릿 로딩
        template_str = self.load_template(doc_request.template_name)

        # 컨텍스트 구성
        context = {
            "research": research_context,
            "participants": participants_context,
            "purpose": doc_request.purpose,
            "published_date": doc_request.published_date
        }

        rendered_document = self.template_renderer.render(template_str, context)
        return rendered_document
    


