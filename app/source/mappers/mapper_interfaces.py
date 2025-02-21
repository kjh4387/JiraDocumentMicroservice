from abc import ABC, abstractmethod
from domain.research import Research  # 도메인 모듈 임포트
from domain.employee import Employee
from domain.company import Company
"""
document_service에서 도메인 객체들에 대한 DIP를 구현하기 위한 mapper interface
"""

class ResearchContextMapper(ABC):
    @abstractmethod
    def to_context(self, research: Research) -> dict:
        pass

class CompanyContextMapper(ABC):
    @abstractmethod
    def to_context(self, research: Research) -> dict:
        pass

class EmployeeContextMapper(ABC):
    @abstractmethod
    def to_context(self, employee: Employee) -> dict:
        pass