from typing import Dict, Any, Optional

class TemplateData:
    """
    Jira API로부터 전달된 raw data + DB 조회 로직을 통해
    최종 치환 가능한 데이터(final_fields)를 완성하는 클래스.
    """
    def __init__(self, template_name: str, raw_fields: Dict[str, Any], domain_data: Optional[Dict[str, Any]] = None):
        """
        :param template_name: 사용할 템플릿 이름 (예: "meeting_expense.html")
        :param raw_fields: Jira request에서 넘어온 필드. 예: {"employee_email": "alice@msimul.com", "purchase_date": "2025-02-10", ...}
        :param domain_data: DB에서 조회 가능한 도메인 데이터 목록. 예: {"employee": {"name": "Alice", "birth": "1990-01-01", ...}, "expense": {"amount": 100000, ...}}
        """
        self.template_name = template_name
        self.raw_fields = raw_fields  # DB가 필요 없는 단순 치환값
        self.final_fields = {}        # 최종적으로 템플릿에 치환할 모든 데이터(= raw_fields + DB 결과)
    
    def prepare_data(self, placeholder_keys: set, db_resolver: "DBResolver"):
        """
        1) 템플릿에서 추출된 placeholder_keys를 확인하고
        2) DB가 필요한 placeholder가 있다면 DBResolver를 통해 추가 데이터를 가져옴
        3) final_fields에 통합
        """
        # 1) 기본적으로 raw_fields를 복사
        self.final_fields = dict(self.raw_fields)

        # 2) placeholder_keys 중 "db:" 프리픽스가 있는 키, 혹은 특정 규칙으로 DB 조회가 필요한 필드 구분
        #    예) "employee.email" / "employee.name" / "employee.birth"
        
        # 예시 규칙: if placeholder_keys에 "employee.email"가 있고, raw_fields{"employee_email"}가 DB 키
        # -> DBResolver를 통해 "employee" 정보를 가져와 final_fields에 병합
        # (아래는 단순 예시)
        
        if "employee.email" in placeholder_keys:
            # raw_fields에 "employee_email"이 있다고 가정
            emp_email = self.raw_fields.get("employee_email")
            if emp_email:
                emp_data = db_resolver.get_employee_by_email(emp_email)
                if emp_data:
                    # emp_data: {"name":..., "signature_path":..., etc.}
                    # final_fields에 병합
                    for k, v in emp_data.items():
                        # placeholder가 "employee.name" 이면 final_fields["employee.name"] = v
                        self.final_fields[f"employee.{k}"] = v
        
        # 3) 시나리오마다 DB 키를 어떻게 구분할지 달라질 수 있음
        #    필요하면 다른 DB 조회(예: "customer_id" -> DB로 customer info)등을 수행
        
        return self.final_fields