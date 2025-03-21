from typing import Dict, Any, List, Optional, Callable, Tuple
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
        
        # 도메인 객체별 조회 방법 정의
        self.domain_resolvers = {
            'company': self._resolve_company,
            'employee': self._resolve_employee, 
            'research': self._resolve_research,
            'expert': self._resolve_expert
        }
        
        # 키 패턴 정의 - 어떤 키가 어떤 도메인 객체를 참조하는지 매핑
        self.key_patterns = {
            # Company 관련 키
            'company_id': 'company',
            'company_name': 'company',
            'supplier_info': 'company',
            'customer_info': 'company',
            
            # Employee 관련 키
            'employee_id': 'employee',
            'email': 'employee',
            'participants': 'employee_list',
            'approval_list': 'employee_list',
            'travel_list': 'employee_list',
            'applicant_info': 'employee',
            'writer_info': 'employee',
            
            # Research 관련 키
            'project_id': 'research',
            'project_code': 'research',
            'research_project_info': 'research',
            
            # Expert 관련 키
            'expert_id': 'expert',
            'expert_info': 'expert',
            '회의_참석자(내부_인원)': 'employee_list',  # 추가
        }
        
        logger.debug("DatabaseDataEnricher initialized")
    
    def enrich(self, document_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 데이터 보강 - 범용적인 방식으로 구현"""
        logger.debug("Enriching document data", document_type=document_type)
        
        # 데이터 복사본 생성
        enriched_data = data.copy()
        
        # 데이터를 재귀적으로 순회하며 보강
        self._enrich_recursive(enriched_data)
        
        logger.debug("Document data enriched successfully", document_type=document_type)
        return enriched_data
    
    def _enrich_recursive(self, data: Any, parent_key: str = None) -> None:
        """데이터를 재귀적으로 순회하며 보강"""
        # 딕셔너리인 경우
        if isinstance(data, dict):
            # 현재 딕셔너리에 대한 보강 처리
            self._enrich_dict(data, parent_key)
            
            # 중첩된 딕셔너리와 리스트에 대한 재귀 처리
            for key, value in list(data.items()):
                self._enrich_recursive(value, key)
                
        # 리스트인 경우
        elif isinstance(data, list):
            # 리스트의 각 항목에 대해 재귀 처리
            for item in data:
                self._enrich_recursive(item, parent_key)
    
    def _enrich_dict(self, data: Dict[str, Any], parent_key: str = None) -> None:
        """딕셔너리 데이터 보강"""
        # 키와 패턴 매칭 확인
        for key in list(data.keys()):
            if key in self.key_patterns:
                domain_type = self.key_patterns[key]
                
                # 단일 객체 보강
                if domain_type in self.domain_resolvers and not domain_type.endswith('_list'):
                    self._enrich_single_entity(data, key, domain_type)
        
        # 전체 딕셔너리가 특정 도메인 객체를 나타내는 경우
        if parent_key in self.key_patterns:
            domain_type = self.key_patterns[parent_key]
            
            # 리스트 객체 보강
            if domain_type.endswith('_list'):
                # 리스트 항목 각각을 보강할 필요는 없음 (재귀에서 처리됨)
                pass
            # 단일 객체이고 딕셔너리 자체가 객체 데이터인 경우
            elif domain_type in self.domain_resolvers:
                self._enrich_entity_dict(data, domain_type)
    
    def _enrich_single_entity(self, data: Dict[str, Any], key: str, domain_type: str) -> None:
        """단일 ID 또는 이름 필드로 엔티티 조회 및 보강"""
        # ID나 이름 같은 단일 값인 경우 (예: "company_id": "COMP-001")
        if key in data and isinstance(data[key], str):
            resolver = self.domain_resolvers[domain_type]
            entity = resolver(data[key])
            
            if entity:
                # 관련된 다른 키 존재 여부 확인 (예: company_id가 있으면 company_name 등도 설정)
                self._update_related_fields(data, entity, key)
    
    def _enrich_entity_dict(self, data: Dict[str, Any], domain_type: str) -> None:
        """엔티티를 나타내는 딕셔너리 보강"""
        resolver = self.domain_resolvers[domain_type]
        entity = None
        
        # 가능한 식별자 키 확인 (company_id, company_name, email 등)
        identifying_keys = self._get_identifying_keys(domain_type)
        
        # 식별자 키 중 하나라도 있으면 엔티티 조회
        for id_key in identifying_keys:
            if id_key in data and data[id_key]:
                entity = resolver(data[id_key])
                if entity:
                    # 엔티티 데이터로 딕셔너리 업데이트
                    self._update_with_entity_data(data, entity, id_key)
                    break
    
    def _get_identifying_keys(self, domain_type: str) -> List[str]:
        """도메인 유형에 따른 식별자 키 목록 반환"""
        if domain_type == 'company':
            return ['company_id', 'company_name']
        elif domain_type == 'employee':
            return ['employee_id', 'email']
        elif domain_type == 'research':
            return ['project_id', 'project_code']
        elif domain_type == 'expert':
            return ['expert_id']
        return []
    
    def _update_with_entity_data(self, data: Dict[str, Any], entity: Any, used_key: str) -> None:
        """엔티티 데이터로 딕셔너리 업데이트"""
        # ID 키 설정 (엔티티 타입에 따라 다름)
        id_key = self._get_id_key_for_entity(entity)
        if id_key and id_key != used_key:
            data[id_key] = entity.id
        
        # 엔티티의 모든 속성을 딕셔너리에 복사
        for key, value in entity.__dict__.items():
            if key != 'id' and value is not None and key not in data:
                data[key] = value
    
    def _get_id_key_for_entity(self, entity: Any) -> Optional[str]:
        """엔티티 타입에 따른 ID 키 반환"""
        if isinstance(entity, Company):
            return 'company_id'
        elif isinstance(entity, Employee):
            return 'employee_id'
        elif isinstance(entity, Research):
            return 'project_id'
        elif isinstance(entity, Expert):
            return 'expert_id'
        return None
    
    def _update_related_fields(self, data: Dict[str, Any], entity: Any, key: str) -> None:
        """관련 필드 업데이트 (예: ID가 있을 때 이름 필드 등 추가)"""
        # company_id가 있으면 company_name 등을 설정
        if key == 'company_id' and isinstance(entity, Company):
            data['company_name'] = entity.company_name
            data['biz_id'] = entity.biz_id
            # 다른 필드 추가 가능
            
        # employee_id가 있으면 name, email 등을 설정
        elif key == 'employee_id' and isinstance(entity, Employee):
            data['name'] = entity.name
            data['email'] = entity.email
            data['department'] = entity.department
            data['position'] = entity.position
            
        # project_id가 있으면 project_code, project_name 등을 설정
        elif key == 'project_id' and isinstance(entity, Research):
            data['project_code'] = entity.project_code
            data['project_name'] = entity.project_name
            data['project_period'] = entity.project_period
            data['project_manager'] = entity.project_manager
            
        # expert_id가 있으면 name 등을 설정
        elif key == 'expert_id' and isinstance(entity, Expert):
            data['name'] = entity.name
            data['affiliation'] = entity.affiliation
            data['position'] = entity.position
    
    # 도메인 객체 조회 메서드들
    def _resolve_company(self, identifier: str) -> Optional[Company]:
        """회사 정보 조회"""
        # ID로 조회
        if identifier.startswith(('COMP-', 'C-')):
            company = self.company_repo.find_by_id(identifier)
            if company:
                logger.debug("Company resolved by ID", id=identifier)
                return company
        
        # 이름으로 조회
        company = self.company_repo.find_by_name(identifier)
        if company:
            logger.debug("Company resolved by name", name=identifier)
            return company
            
        logger.warning("Company not found", identifier=identifier)
        return None
    
    def _resolve_employee(self, identifier: str) -> Optional[Employee]:
        """직원 정보 조회"""
        # ID로 조회
        if identifier.startswith(('EMP-', 'E-')):
            employee = self.employee_repo.find_by_id(identifier)
            if employee:
                logger.debug("Employee resolved by ID", id=identifier)
                return employee
        
        # 이메일로 조회
        if '@' in identifier:
            employee = self.employee_repo.find_by_email(identifier)
            if employee:
                logger.debug("Employee resolved by email", email=identifier)
                return employee
                
        logger.warning("Employee not found", identifier=identifier)
        return None
    
    def _resolve_research(self, identifier: str) -> Optional[Research]:
        """연구 과제 정보 조회"""
        # ID로 조회
        if identifier.startswith(('RESEARCH-', 'R-')):
            research = self.research_repo.find_by_id(identifier)
            if research:
                logger.debug("Research project resolved by ID", id=identifier)
                return research
        
        # 코드로 조회
        research = self.research_repo.find_by_project_code(identifier)
        if research:
            logger.debug("Research project resolved by code", code=identifier)
            return research
            
        logger.warning("Research project not found", identifier=identifier)
        return None
    
    def _resolve_expert(self, identifier: str) -> Optional[Expert]:
        """전문가 정보 조회"""
        # ID로 조회
        expert = self.expert_repo.find_by_id(identifier)
        if expert:
            logger.debug("Expert resolved by ID", id=identifier)
            return expert
            
        logger.warning("Expert not found", identifier=identifier)
        return None
