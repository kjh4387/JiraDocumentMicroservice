from typing import Dict, Any, List
from app.source.core.interfaces import DataEnricher, Repository
from app.source.core.domain import Company, Employee, Research, Expert
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class DataEnricher:
    """데이터 보강 서비스"""
    
    def __init__(self, company_repository, employee_repository, 
                research_repository, expert_repository):
        self.company_repository = company_repository
        self.employee_repository = employee_repository
        self.research_repository = research_repository
        self.expert_repository = expert_repository
        logger.debug("DataEnricher initialized")
    
    def enrich_company_data(self, company_id: str, data: dict) -> dict:
        """회사 데이터 보강"""
        try:
            company = self.company_repository.find_one({"id": company_id})
            if company:
                data["company_info"] = {
                    "name": company.get("name"),
                    "address": company.get("address"),
                    "business_number": company.get("business_number"),
                    "representative": company.get("representative"),
                    "tel": company.get("tel"),
                    "fax": company.get("fax"),
                    "email": company.get("email")
                }
                logger.debug("Company data enriched", company_id=company_id)
            else:
                logger.warning("Company not found", company_id=company_id)
        except Exception as e:
            logger.error(f"Failed to enrich company data: {str(e)}", company_id=company_id)
        
        return data
    
    def enrich_employee_data(self, employee_id: str, data: dict) -> dict:
        """직원 데이터 보강"""
        try:
            employee = self.employee_repository.find_one({"id": employee_id})
            if employee:
                data["employee_info"] = {
                    "name": employee.get("name"),
                    "employee_id": employee.get("employee_id"),
                    "department": employee.get("department"),
                    "position": employee.get("position"),
                    "email": employee.get("email"),
                    "contact": employee.get("contact"),
                    "signature_image_url": employee.get("signature_image_url")
                }
                logger.debug("Employee data enriched", employee_id=employee_id)
            else:
                logger.warning("Employee not found", employee_id=employee_id)
        except Exception as e:
            logger.error(f"Failed to enrich employee data: {str(e)}", employee_id=employee_id)
            
        return data
    
    def enrich_research_data(self, research_id: str, data: dict) -> dict:
        """연구 프로젝트 데이터 보강"""
        try:
            research = self.research_repository.find_one({"id": research_id})
            if research:
                data["research_info"] = {
                    "name": research.get("name"),
                    "code": research.get("code"),
                    "period": research.get("period"),
                    "budget": research.get("budget"),
                    "manager": research.get("manager"),
                    "description": research.get("description")
                }
                logger.debug("Research data enriched", research_id=research_id)
            else:
                logger.warning("Research not found", research_id=research_id)
        except Exception as e:
            logger.error(f"Failed to enrich research data: {str(e)}", research_id=research_id)
            
        return data
    
    def enrich_expert_data(self, expert_id: str, data: dict) -> dict:
        """전문가 데이터 보강"""
        try:
            expert = self.expert_repository.find_one({"id": expert_id})
            if expert:
                data["expert_info"] = {
                    "name": expert.get("name"),
                    "affiliation": expert.get("affiliation"),
                    "position": expert.get("position"),
                    "specialty": expert.get("specialty"),
                    "contact": expert.get("contact"),
                    "email": expert.get("email"),
                    "bank_account": expert.get("bank_account")
                }
                logger.debug("Expert data enriched", expert_id=expert_id)
            else:
                logger.warning("Expert not found", expert_id=expert_id)
        except Exception as e:
            logger.error(f"Failed to enrich expert data: {str(e)}", expert_id=expert_id)
            
        return data
    
    def enrich_approval_list(self, approver_ids: list, data: dict) -> dict:
        """결재자 목록 데이터 보강"""
        approval_list = []
        
        for i, employee_id in enumerate(approver_ids):
            try:
                employee = self.employee_repository.find_one({"id": employee_id})
                if employee:
                    approval_list.append({
                        "order": i + 1,
                        "name": employee.get("name"),
                        "employee_id": employee.get("employee_id"),
                        "department": employee.get("department"),
                        "position": employee.get("position"),
                        "signature_image_url": employee.get("signature_image_url"),
                        "status": "pending"
                    })
                    logger.debug("Approver enriched with employee data", 
                                employee_id=employee_id, index=i)
            except Exception as e:
                logger.error(f"Failed to enrich approver data: {str(e)}", 
                           employee_id=employee_id, index=i)
        
        data["approval_list"] = approval_list
        return data
