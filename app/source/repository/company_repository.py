from domain.company import Company

class CompanyRepository:
    def get_by_email(self, email: str) -> Company:
        # 데모 return
        return Company(
            email=email,
            name="John Doe",            
        )
