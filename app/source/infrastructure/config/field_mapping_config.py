from typing import Dict, Any, List
import yaml
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EnrichField:
    name: str

@dataclass
class FieldPattern:
    type: str
    enrich_fields: List[EnrichField]
    is_list: bool = False
    value_key: str = None  # 딕셔너리 필드에서 사용할 값의 키

@dataclass
class DomainConfig:
    query_key: str
    id_field: str

class FieldMappingConfig:
    """필드 매핑 설정을 관리하는 클래스"""
    
    def __init__(self, config_path: str = None):
        """초기화
        
        Args:
            config_path: YAML 설정 파일 경로. 기본값은 'config/field_mapping.yaml'
        """
        if config_path is None:
            # 프로젝트 루트 디렉토리 기준으로 설정 파일 경로 계산
            current_dir = Path(__file__).parent.parent.parent
            config_path = os.path.join(current_dir, 'config', 'field_mapping.yaml')
            
        self.config_path = config_path
        self.field_patterns: Dict[str, FieldPattern] = {}
        self.domain_configs: Dict[str, DomainConfig] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """YAML 설정 파일을 로드하고 파싱"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 도메인 설정 파싱
            for domain_type, domain_data in config.get('domain_config', {}).items():
                self.domain_configs[domain_type] = DomainConfig(
                    query_key=domain_data['query_key'],
                    id_field=domain_data['id_field']
                )
            
            # 필드 패턴 파싱
            for pattern_name, pattern_data in config.get('field_patterns', {}).items():
                enrich_fields = [
                    EnrichField(name=field['name'])
                    for field in pattern_data['enrich_fields']
                ]
                self.field_patterns[pattern_name] = FieldPattern(
                    type=pattern_data['type'],
                    enrich_fields=enrich_fields,
                    is_list=pattern_data.get('is_list', False),
                    value_key=pattern_data.get('value_key')  # 값 키 파싱 추가
                )
                
        except Exception as e:
            raise RuntimeError(f"Failed to load field mapping config from {self.config_path}: {str(e)}")
    
    def get_field_pattern(self, pattern_name: str) -> FieldPattern:
        """필드 패턴 조회
        
        Args:
            pattern_name: 패턴 이름
            
        Returns:
            FieldPattern 객체
        """
        return self.field_patterns.get(pattern_name)
    
    def get_domain_config(self, domain_type: str) -> DomainConfig:
        """도메인 설정 조회
        
        Args:
            domain_type: 도메인 타입
            
        Returns:
            DomainConfig 객체
        """
        return self.domain_configs.get(domain_type)
    
    def get_all_field_patterns(self) -> Dict[str, FieldPattern]:
        """모든 필드 패턴 조회
        
        Returns:
            필드 패턴 딕셔너리
        """
        return self.field_patterns
    
    def get_all_domain_configs(self) -> Dict[str, DomainConfig]:
        """모든 도메인 설정 조회
        
        Returns:
            도메인 설정 딕셔너리
        """
        return self.domain_configs 