# 파일명: test_document_generation.py

import pytest
from weasyprint import HTML

from pathlib import Path
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from services.document_service import DocumentService, DocumentRequest
import logging
import logger_settings


@pytest.fixture
def document_service() -> DocumentService:
    """
    테스트용 DocumentService 인스턴스 생성 (Repository는 목업).
    """
    research_repo = ResearchRepository()
    employee_repo = EmployeeRepository()

    template_dir = os.path.join(os.path.dirname(__file__), "testdata")
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)

    return DocumentService(research_repo, employee_repo, template_dir, logger=logger)


def test_template_loading(document_service: DocumentService):
    """
    DocumentService를 통해 템플릿이 올바르게 로딩되는지 테스트합니다.
    - 템플릿 파일이 정상적으로 로드되어야 합니다.
    """
    template_name = "2. 출장신청서_20240924 - 복사본.html"
    template_str = document_service.load_template(template_name)
    
    assert "출 장 신 청 서" in template_str


def test_template_rendering(document_service: DocumentService):
    """
    DocumentService를 통해 HTML 문서가 올바르게 렌더링되는지 테스트합니다.
    - 연구 정보, 참석자 정보, 목적, 작성일 등이 올바른 형태로 포함되어야 합니다.
    """
    # 테스트용 입력 데이터 (Jira에서 전송받은 데이터 모의)
    doc_request = DocumentRequest(
        template_name="2. 출장신청서_20240924 - 복사본.html",
        research_key="R123",
        participants=["bob@example.com","charlie@example.com","alice@example.com"],
        purpose="출장 회의",
        published_date="2024-09-24"
    )

    rendered_html = document_service.create_document(doc_request)
    
    # 더미 ResearchRepository는 "Research Project Example"을 반환합니다.
    assert "Research Project Example" in rendered_html
    # 더미 EmployeeRepository는 모든 참석자에 대해 "John Doe"와 "signature_placeholder"를 반환합니다.
    assert rendered_html.count("John Doe") == 3
    assert "출장 회의" in rendered_html
    assert "2024-09-24" in rendered_html


def test_weasyprint_pdf_generation(document_service: DocumentService):
    """
    렌더링된 HTML을 WeasyPrint를 이용해 PDF로 변환할 때 예외 없이 결과물이 생성되는지 테스트합니다.
    PDF의 byte 크기가 일정 수준 이상이면 정상적으로 변환되었다고 볼 수 있습니다.
    """
    doc_request = DocumentRequest(
        research_key="R123",
        participant1_email="alice@example.com",
        participant2_email="bob@example.com",
        participant3_email="charlie@example.com",
        purpose="출장 회의",
        published_date="2024-09-24"
    )

    rendered_html = document_service.create_document(doc_request)
    
    # WeasyPrint로 PDF 생성
    pdf_bytes = HTML(string=rendered_html).write_pdf()
    
    # PDF 파일은 보통 일정 크기 이상이어야 함 (예: 1KB 미만이면 이상)
    assert len(pdf_bytes) > 1024


import re

from domain.company import Company
class CompanyRepository:
    def get_by_email(self, email: str) -> Company:
        # 데모 return
        return Company(
            email=email,
            name="메테오 시뮬레이션",            
        )
    
from domain.employee import Employee

class EmployeeRepository:
    def get_by_email(self, email: str) -> Employee:
        # 데모 return
        return Employee(
            email=email,
            name="John Doe",            # 이메일에 따른 실제 이름을 DB에서 조회
            bank_account=bank_account( "400000-00-0120344","국민"),
            department = "개발부",
            position = "주임연구원",
            affiliation_id = "000",
            signature_path="app/data/testdata/2. 출장신청서_20240924 - 복사본_hd1.png" # 서명 이미지 URL 또는 데이터
        )

from domain.research import Research
from datetime import date
from domain.bank_account import bank_account
class ResearchRepository:
    def get_by_key(self, research_key: str) -> Research:
        #데모 return
        return Research(
            research_key=research_key,
            research_name="Research Project Example",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )


