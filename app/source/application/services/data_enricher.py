from typing import Dict, Any, List
from app.source.core.interfaces import DataEnricher, Repository
from app.source.core.domain import Company, Employee, Research, Expert
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class DatabaseDataEnricher(DataEnricher):
    """데이터베이스를 사용한 문서 데이터 보강"""
    
    def __init__(
        self,
        company_repo: Repository[Company],
        employee_repo: Repository[Employee],
        research_repo: Repository[Research],
        expert_repo: Repository[Expert]
    ):
        self.company_repo = company_repo
        self.employee_repo = employee_repo
        self.research_repo = research_repo
        self.expert_repo = expert_repo
        logger.debug("DatabaseDataEnricher initialized")
    
    def enrich(self, document_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 데이터 보강"""
        logger.debug("Enriching document data", document_type=document_type)
        
        # 데이터 복사본 생성
        enriched_data = data.copy()
        
        # 문서 유형별 보강 로직
        if document_type in ["견적서", "거래명세서"]:
            self._enrich_supplier_info(enriched_data.get("supplier_info", {}))
        
        if document_type in ["출장신청서", "출장정산신청서", "회의비사용신청서", "회의록"]:
            self._enrich_participants(enriched_data.get("participants", []))
            self._enrich_research_project(enriched_data.get("research_project_info", {}))
        
        if document_type in ["전문가활용계획서", "전문가자문확인서"]:
            self._enrich_expert_info(enriched_data.get("expert_info", {}))
            self._enrich_research_project(enriched_data.get("research_project_info", {}))
        
        if "approval_list" in enriched_data:
            self._enrich_approval_list(enriched_data["approval_list"])
        
        logger.debug("Document data enriched successfully", document_type=document_type)
        return enriched_data
    
    def _enrich_supplier_info(self, supplier_info: Dict[str, Any]) -> None:
        """공급자 정보 보강"""
        if not supplier_info:
            return
            
        logger.debug("Enriching supplier info")
        
        if "company_id" in supplier_info:
            company_id = supplier_info["company_id"]
            company = self.company_repo.find_by_id(company_id)
            
            if company:
                # ID는 유지하고 나머지 정보 업데이트
                for key, value in company.__dict__.items():
                    if key != "id" and value is not None:
                        supplier_info[key] = value
                
                logger.debug("Supplier info enriched with company data", company_id=company_id)
    
    def _enrich_participants(self, participants: List[Dict[str, Any]]) -> None:
        """참가자 정보 보강"""
        if not participants:
            return
            
        logger.debug("Enriching participants", count=len(participants))
        
        for i, participant in enumerate(participants):
            if "employee_id" in participant:
                employee_id = participant["employee_id"]
                employee = self.employee_repo.find_by_id(employee_id)
                
                if employee:
                    # ID는 유지하고 나머지 정보 업데이트
                    for key, value in employee.__dict__.items():
                        if key != "id" and value is not None:
                            participant[key] = value
                    
                    logger.debug("Participant enriched with employee data", 
                                employee_id=employee_id, index=i)
    
    def _enrich_research_project(self, research_info: Dict[str, Any]) -> None:
        """연구 과제 정보 보강"""
        if not research_info:
            return
            
        logger.debug("Enriching research project info")
        
        if "project_id" in research_info:
            project_id = research_info["project_id"]
            research = self.research_repo.find_by_id(project_id)
            
            if research:
                # ID는 유지하고 나머지 정보 업데이트
                for key, value in research.__dict__.items():
                    if key != "id" and value is not None:
                        research_info[key] = value
                
                logger.debug("Research project info enriched", project_id=project_id)
    
    def _enrich_expert_info(self, expert_info: Dict[str, Any]) -> None:
        """전문가 정보 보강"""
        if not expert_info:
            return
            
        logger.debug("Enriching expert info")
        
        if "expert_id" in expert_info:
            expert_id = expert_info["expert_id"]
            expert = self.expert_repo.find_by_id(expert_id)
            
            if expert:
                # ID는 유지하고 나머지 정보 업데이트
                for key, value in expert.__dict__.items():
                    if key != "id" and value is not None:
                        expert_info[key] = value
                
                logger.debug("Expert info enriched", expert_id=expert_id)
    
    def _enrich_approval_list(self, approval_list: List[Dict[str, Any]]) -> None:
        """결재자 정보 보강"""
        if not approval_list:
            return
            
        logger.debug("Enriching approval list", count=len(approval_list))
        
        for i, approver in enumerate(approval_list):
            if "employee_id" in approver:
                employee_id = approver["employee_id"]
                employee = self.employee_repo.find_by_id(employee_id)
                
                if employee:
                    # 직원 정보로 결재자 정보 업데이트
                    approver["name"] = employee.name
                    approver["department"] = employee.department
                    approver["position"] = employee.position
                    
                    # 서명 이미지가 있으면 추가
                    if employee.signature:
                        approver["signature"] = employee.signature
                    
                    logger.debug("Approver enriched with employee data", 
                                employee_id=employee_id, index=i)
