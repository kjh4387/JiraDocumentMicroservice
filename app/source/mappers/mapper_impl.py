from .mapper_interfaces import *


class DefaultResearchContextMapper(ResearchContextMapper):
    def to_context(self, research: Research) -> dict:
        return research.__dict__
    
class DefaultCompanyContextMapper(CompanyContextMapper):
    def to_context(self, company: Company) -> dict:
        return company.__dict__

class DefaultEmployeeContextMapper(EmployeeContextMapper):
    def to_context(self, employee: Employee) -> dict:
        return employee.__dict__
