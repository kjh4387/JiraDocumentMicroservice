from typing import Dict, Any, List, Optional, Callable, Tuple
from app.source.core.interfaces import DataEnricher, Repository
from app.source.core.domain import Company, Employee, Research, Expert
import logging
from app.source.infrastructure.repositories.company_repo_v2 import CompanyRepositoryV2
from app.source.infrastructure.repositories.employee_repo_v2 import EmployeeRepositoryV2
from app.source.infrastructure.repositories.research_repo_v2 import ResearchRepositoryV2
from app.source.infrastructure.repositories.expert_repo_v2 import ExpertRepositoryV2
from app.source.infrastructure.config.field_mapping_config import FieldMappingConfig

logger = logging.getLogger(__name__)

class SelectiveFieldEnricher(DataEnricher):
    """필드 ID 패턴 기반 데이터 보강 - Jira 응답 구조 유지"""
    
    def __init__(
        self,
        company_repo: CompanyRepositoryV2,
        employee_repo: EmployeeRepositoryV2,
        research_repo: ResearchRepositoryV2,
        expert_repo: ExpertRepositoryV2,
        field_mapping_config: Optional[FieldMappingConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.company_repo = company_repo
        self.employee_repo = employee_repo
        self.research_repo = research_repo
        self.expert_repo = expert_repo
        self.field_mapping_config = field_mapping_config or FieldMappingConfig()
        self.logger = logger or logging.getLogger(__name__)
        
        # 도메인 객체 타입별 리포지토리 매핑
        self.repo_by_type = {
            'company': self.company_repo,
            'employee': self.employee_repo,
            'research': self.research_repo,
            'expert': self.expert_repo
        }
        
        self.logger.debug("SelectiveFieldEnricher initialized with field mapping config")
        self.logger.debug("Available repositories: %s", list(self.repo_by_type.keys()))
    
    def _find_entity(self, repo: Repository, domain_type: str, value: str) -> Optional[Any]:
        """도메인 객체 조회
        
        Args:
            repo: 리포지토리 객체
            domain_type: 도메인 객체 타입
            value: 조회할 값
            
        Returns:
            도메인 객체 또는 None
        """
        try:
            domain_config = self.field_mapping_config.get_domain_config(domain_type)
            if not domain_config:
                self.logger.error("No domain config found for type: %s", domain_type)
                return None
                
            query_key = domain_config.query_key
            self.logger.debug("Finding %s with %s: %s", domain_type, query_key, value)
            
            # 리포지토리 메서드 이름 동적 생성 (예: find_by_name, find_by_account_id 등)
            find_method = f"find_by_{query_key}"
            if not hasattr(repo, find_method):
                self.logger.error("Repository %s has no method %s", repo.__class__.__name__, find_method)
                return None
            self.logger.debug("Found method %s in repository %s", find_method, repo.__class__.__name__)
            find_func = getattr(repo, find_method)
            entity = find_func(value)
            
            if entity:
                self.logger.debug("Found %s: %s", domain_type, entity)
            else:
                self.logger.warning("No %s found with %s: %s", domain_type, query_key, value)
                
            return entity
            
        except Exception as e:
            self.logger.error("Error finding %s with %s: %s", domain_type, query_key, str(e))
            return None
    
    def _enrich_field(self, fields: Dict[str, Any], field_name: str, field_value: Any, pattern: Any) -> None:
        """일반 필드 보강
        
        Args:
            fields: 필드 데이터 딕셔너리
            field_name: 현재 처리 중인 필드 이름
            field_value: 필드 값
            pattern: 필드 패턴 설정
        """
        try:
            self.logger.debug("Enriching field: %s (value: %s) with pattern type: %s", 
                            field_name, field_value, pattern.type)
            
            # 도메인 객체 조회
            repo = self.repo_by_type.get(pattern.type)
            if not repo:
                self.logger.error("No repository found for type: %s", pattern.type)
                return
            
            # 필드가 딕셔너리이고 value_key가 지정된 경우 해당 키의 값 사용
            actual_value = field_value
            field_is_dict = isinstance(field_value, dict)
            
            if field_is_dict and pattern.value_key:
                if pattern.value_key in field_value:
                    actual_value = field_value[pattern.value_key]
                    self.logger.debug("Using value from key '%s': %s", pattern.value_key, actual_value)
                else:
                    self.logger.warning("Key '%s' not found in field value: %s", pattern.value_key, field_value)
                    return
            
            # 도메인 객체 조회
            entity = self._find_entity(repo, pattern.type, str(actual_value))
            if not entity:
                return
            
            # 보강 필드 추가
            # 필드가 딕셔너리가 아니면 딕셔너리로 변환
            if not field_is_dict:
                # 원본 값 저장
                enriched_dict = {
                    "value": field_value,
                    "id": getattr(entity, "id", None)
                }
                # fields 딕셔너리에 업데이트된 값 설정
                fields[field_name] = enriched_dict
                self.logger.debug("Converted field %s to dictionary: %s", field_name, enriched_dict)
            else:
                enriched_dict = field_value
            
            # 보강 필드 추가 (딕셔너리 내부에 추가)
            for enrich_field in pattern.enrich_fields:
                field_value = getattr(entity, enrich_field.name, None)
                if field_value is not None:
                    enriched_dict[enrich_field.name] = field_value
                    self.logger.debug("Added enriched field: %s = %s", enrich_field.name, field_value)
                else:
                    self.logger.debug("No value found for field: %s", enrich_field.name)
            
            self.logger.debug("Completed enriching %s info for %s", pattern.type, field_name)
            
        except Exception as e:
            self.logger.error("Error enriching field %s: %s", field_name, str(e))
    
    def _enrich_list_field(self, fields: Dict[str, Any], field_name: str, field_value: List[Any], pattern: Any) -> None:
        """리스트 타입 필드 보강
        
        Args:
            fields: 필드 데이터 딕셔너리
            field_name: 현재 처리 중인 필드 이름
            field_value: 필드 값 (리스트)
            pattern: 필드 패턴 설정
        """
        try:
            self.logger.debug("Enriching list field: %s with %d items", field_name, len(field_value))
            
            # 도메인 객체 조회를 위한 리포지토리 가져오기
            repo = self.repo_by_type.get(pattern.type)
            if not repo:
                self.logger.error("No repository found for type: %s", pattern.type)
                return
            
            # 도메인 설정 가져오기
            domain_config = self.field_mapping_config.get_domain_config(pattern.type)
            if not domain_config:
                self.logger.error("No domain config found for type: %s", pattern.type)
                return
            
            # 리스트의 각 항목에 대해 보강 수행
            for i, item in enumerate(field_value):
                self.logger.debug("Processing list item %d: %s", i, item)
                
                if not isinstance(item, dict):
                    self.logger.warning("List item %d is not a dictionary, skipping", i)
                    continue
                
                # ID 필드가 있는지 확인
                if domain_config.id_field not in item:
                    self.logger.warning("No %s found in list item %d", domain_config.id_field, i)
                    continue
                
                # 도메인 객체 조회
                entity = self._find_entity(repo, pattern.type, str(item[domain_config.id_field]))
                if not entity:
                    continue
                
                # 보강 필드 추가
                for enrich_field in pattern.enrich_fields:
                    field_value = getattr(entity, enrich_field.name, None)
                    if field_value is not None:
                        item[enrich_field.name] = field_value
                        self.logger.debug("Added enriched field: %s = %s", enrich_field.name, field_value)
                    else:
                        self.logger.debug("No value found for field: %s", enrich_field.name)
            
            self.logger.debug("Completed enriching list field: %s", field_name)
            
        except Exception as e:
            self.logger.error("Error enriching list field %s: %s", field_name, str(e))

    def enrich(self, document_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 데이터 보강
        
        Args:
            document_type: 문서 타입 (사용하지 않음)
            data: 보강할 데이터
            
        Returns:
            보강된 데이터
        """
        try:
            self.logger.debug("Starting data enrichment")
            
            # 모든 필드 패턴 가져오기
            field_patterns = self.field_mapping_config.get_all_field_patterns()
            if not field_patterns:
                self.logger.warning("No field patterns found in configuration")
                return data
            
            self.logger.debug("Field patterns loaded: %d patterns", len(field_patterns))
            
            # 데이터 복사본 생성
            enriched_data = data.copy()
            
            # 필드에 직접 접근할지 또는 'fields' 키를 통해 접근할지 결정
            fields_dict = enriched_data.get('fields', enriched_data)
            
            # 각 필드에 대해 보강 수행
            for field_name, field_value in fields_dict.items():
                # 필드 이름이 패턴 목록에 있는지 확인
                pattern = field_patterns.get(field_name)
                if not pattern:
                    self.logger.debug("No pattern found for field: %s", field_name)
                    continue
                
                self.logger.debug("Pattern found for field %s: type=%s, is_list=%s, value_key=%s", 
                               field_name, pattern.type, pattern.is_list, pattern.value_key)
                
                # 리스트 타입 필드 처리
                if pattern.is_list and isinstance(field_value, list):
                    self._enrich_list_field(fields_dict, field_name, field_value, pattern)
                # 일반 필드 처리
                else:
                    self._enrich_field(fields_dict, field_name, field_value, pattern)
            
            self.logger.debug("Completed data enrichment")
            return enriched_data
            
        except Exception as e:
            self.logger.error("Error during data enrichment: %s", str(e))
            return data


# 기존 클래스 유지하되 deprecated 표시
class DatabaseDataEnricher(DataEnricher):
    """(Deprecated) 기존 데이터베이스 보강 로직 - 이전 버전과의 호환성을 위해 유지"""
    
    def __init__(
        self,
        company_repo: CompanyRepositoryV2,
        employee_repo: EmployeeRepositoryV2,
        research_repo: ResearchRepositoryV2,
        expert_repo: ExpertRepositoryV2,
        logger: Optional[logging.Logger] = None
    ):
        self.company_repo = company_repo
        self.employee_repo = employee_repo
        self.research_repo = research_repo
        self.expert_repo = expert_repo
        self.logger = logger or logging.getLogger(__name__)
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
            'internal_participants': 'employee_list',
            'approval_list': 'employee_list',
            'travel_list': 'employee_list',
            'applicant_info': 'employee',
            'writer_info': 'employee',
            'jira_account_id': 'employee',
            
            # Research 관련 키
            'project_id': 'research',
            'project_code': 'research',
            'research_project_info': 'research',
            
            'expert_id': 'expert',
            'expert_info': 'expert',
        }
        
        self.logger.warning("Using deprecated DatabaseDataEnricher - please migrate to SelectiveFieldEnricher")
        
    def enrich(self, document_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """기존 enrich 메서드로 호환성 유지를 위해 그대로 둠
        하지만 더 이상 사용되지 않으므로 경고 로그 출력
        """
        self.logger.warning("Using deprecated DatabaseDataEnricher.enrich method. Consider migrating to SelectiveFieldEnricher.")
        
        return data
