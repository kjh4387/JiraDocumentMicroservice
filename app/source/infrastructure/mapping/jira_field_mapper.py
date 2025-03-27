from typing import Dict, Any
import os
import json
import logging
from app.source.core.interfaces import JiraFieldMappingProvider, JiraFieldMapper

logger = logging.getLogger(__name__)
class ApiJiraFieldMappingProvider(JiraFieldMappingProvider):
    """Jira API에서 필드 매핑 데이터를 가져오는 제공자"""
    
    def __init__(self, jira_api_client, logger: logging.Logger = None):
        self.jira_api_client = jira_api_client
        self.field_mappings = {}
        self.initialized = False
        self.logger = logger or logging.getLogger(__name__)
    
    def get_field_mapping(self) -> Dict[str, str]:
        if not self.initialized:
            self.refresh()
        return self.field_mappings
    
    def refresh(self) -> None:
        try:
            # Jira API를 통해 필드 정보 가져오기
            response = self.jira_api_client._make_request('GET', '/rest/api/2/field')
            
            # 매핑 구성
            mappings = {}
            for field in response:
                if 'key' in field and 'name' in field:
                    field_id = field['key']
                    # 사람이 읽기 쉬운 형식으로 변환
                    field_name = field['name'].lower().replace(' ', '_')
                    mappings[field_id] = field_name
            
            self.field_mappings = mappings
            self.initialized = True
            self.logger.info("Field mappings loaded from Jira API")
            
        except Exception as e:
            self.logger.error("Failed to load field mappings from API: %s", str(e))
            # 실패 시 빈 매핑 사용
            self.field_mappings = {}
            self.initialized = True

    def get_field_mapping_file_path(self) -> str:
        """필드 매핑 파일 경로 반환"""
        return os.environ.get(
            'JIRA_FIELD_MAPPING', 
            '/workspace/app/config/jira_field_mapping.json'
        )
    

class FileJiraFieldMappingProvider(JiraFieldMappingProvider):
    """파일에서 필드 매핑 데이터를 로드하는 제공자"""
    
    def __init__(self, file_path=None, logger: logging.Logger = None):
        self.file_path = file_path or os.environ.get(
            'JIRA_FIELD_MAPPING', 
            '/workspace/app/config/jira_field_mapping.json'
        )
        self.field_mappings = {}
        self.initialized = False
        self.logger = logger or logging.getLogger(__name__)
    
    def get_field_mappings(self) -> Dict[str, str]:
        if not self.initialized:
            self.refresh()
        return self.field_mappings
    
    def refresh(self) -> None:
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    self.field_mappings = json.load(f)
                self.logger.info("Field mappings loaded from %s", self.file_path)
            else:
                self.logger.warning("Mapping file not found: %s", self.file_path)
                self.field_mappings = {}
            
            self.initialized = True
            
        except Exception as e:
            self.logger.error("Failed to load field mappings from file: %s", str(e))
            self.field_mappings = {}
            self.initialized = True

class JiraFieldMapperimpl(JiraFieldMapper):
    """Jira 필드 ID를 사람이 읽을 수 있는 이름으로 매핑"""
    
    def __init__(self, mapping_provider: JiraFieldMappingProvider = None, logger: logging.Logger = None):
        self.mapping_provider = mapping_provider
        self.logger = logger or logging.getLogger(__name__)
    
    def set_mapping_provider(self, provider: JiraFieldMappingProvider):
        """런타임에 매핑 제공자 변경"""
        self.mapping_provider = provider
    
    def map_field_id_to_name(self, field_id: str) -> str:
        """필드 ID를 이름으로 변환"""
        if not field_id.startswith('customfield_'):
            return field_id
            
        mappings = self.mapping_provider.get_field_mapping()
        return mappings.get(field_id, field_id)
    
    def map_field_name_to_id(self, field_name: str) -> str:
        """이름을 필드 ID로 변환 (역매핑)"""
        mappings = self.mapping_provider.get_field_mapping()
        reverse_mapping = {v: k for k, v in mappings.items()}
        return reverse_mapping.get(field_name, field_name)
    
    def transform_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """응답 데이터의 필드 키를 변환"""
        if 'fields' not in response_data:
            return response_data
            
        transformed = response_data.copy()
        mapped_fields = {}
        
        for field_id, value in response_data['fields'].items():
            if field_id.startswith('customfield_'):
                field_name = self.map_field_id_to_name(field_id)
                mapped_fields[field_name] = value
            else:
                mapped_fields[field_id] = value
                
        transformed['fields'] = mapped_fields
        return transformed
    
    def refresh_mappings(self):
        """매핑 데이터 새로고침"""
        self.mapping_provider.refresh()