from domain.employee import Employee

class EmployeeRepository:
    def get_by_email(self, email: str) -> Employee:
        # 데모 return
        return Employee(
            email=email,
            name="John Doe",            # 이메일에 따른 실제 이름을 DB에서 조회
            sign="signature_placeholder" # 서명 이미지 URL 또는 데이터
        )
