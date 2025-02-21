from datetime import date

class Research:
    def __init__(self,  project_key: str, project_title:str, start_date : date, end_date : date,business_name: str = "", ministry_name: str= "", agency_name: str= "", insitution_role:str= "", project_summary:str= "", research_budget:int= 0, progress_status:str= ""):
        """
        project_key: 과제 번호
        project_title: 연구개발 과제명
        progress_status: 수행 진행 구분(진행상태)
        business_name: 사업명
        ministry_name: 부처명
        agency_name: 전문기관 명
        institution_role: 연구기관 역할 구분
        project_summary:연구개발 내용 요약
        research_budget:연구개발비(백만원)
        start_date: 연구 시작일
        end_date: 연구 종료일
        """
        self.project_key = project_key
        self.project_title = project_title
        self.start_data = start_date
        self.end_date = end_date
        self.business_name = business_name
        self.ministry_name = ministry_name
        self.agency_name = agency_name
        self.institution_role = insitution_role
        self.project_summary = project_summary
        self.research_budget = research_budget
        self.progress_status = progress_status

