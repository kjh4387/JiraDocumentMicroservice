from repository.research_repository import ResearchRepository
from repository.employee_repository import EmployeeRepository
from services.template_renderer import TemplateRenderer
from datetime import date
from pydantic import BaseModel

# 요청 데이터에 대한 Pydantic 모델 (확장 가능)
class DocumentRequest(BaseModel):
    research_key: str
    participant1_email: str
    participant2_email: str
    participant3_email: str
    purpose: str
    published_date: date  # 실제 사용 시 date 형식으로 변환할 수도 있음

class DocumentService:
    def __init__(self, research_repo: ResearchRepository, employee_repo: EmployeeRepository):
        self.research_repo = research_repo
        self.employee_repo = employee_repo
        self.template_renderer = TemplateRenderer()

    def create_document(self, doc_request: DocumentRequest) -> str:
        # 1. DB 조회: Research 정보
        research = self.research_repo.get_by_key(doc_request.research_key)
        # 2. DB 조회: 각 참가자 정보
        participant1 = self.employee_repo.get_by_email(doc_request.participant1_email)
        participant2 = self.employee_repo.get_by_email(doc_request.participant2_email)
        participant3 = self.employee_repo.get_by_email(doc_request.participant3_email)

        # 3. 템플릿 컨텍스트 구성 (Jira 이슈에서 받은 값과 DB에서 조회한 값을 혼합)
        context = {
            "research": {
                "name": research.name,
                "start_date": research.start_date.strftime("%Y.%m.%d"),
                "end_date": research.end_date.strftime("%Y.%m.%d")
            },
            "participant1": {
                "name": participant1.name,
                "signature": participant1.sign
            },
            "participant2": {
                "name": participant2.name,
                "signature": participant2.sign
            },
            "participant3": {
                "name": participant3.name,
                "signature": participant3.sign
            },
            "purpose": doc_request.purpose,         # 직접 입력받은 값
            "published_date": doc_request.published_date
        }

        # 4. 템플릿 선택
        # 추후 이슈 유형별로 여러 템플릿 핸들러(Strategy 패턴)로 확장 가능함.
        template_str = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>서류 자동 작성</title>
</head>
<body>
  <h1>{{ research.name }}</h1>
  <p>연구 기간: {{ research.start_date }} ~ {{ research.end_date }}</p>
  <h2>참석자</h2>
  <ul>
    <li>이름: {{ participant1.name }}, 서명: {{ participant1.signature }}</li>
    <li>이름: {{ participant2.name }}, 서명: {{ participant2.signature }}</li>
    <li>이름: {{ participant3.name }}, 서명: {{ participant3.signature }}</li>
  </ul>
  <p>출장 목적: {{ purpose }}</p>
  <p>문서 작성일: {{ published_date }}</p>
</body>
</html>
"""

        # 5. 템플릿 렌더링
        rendered_document = self.template_renderer.render(template_str, context)
        # (추후 document_log 테이블에 기록하는 기능 추가 가능)
        return rendered_document
