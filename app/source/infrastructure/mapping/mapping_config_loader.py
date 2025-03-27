import os
import yaml
import logging
from typing import Dict, Any, Optional

class MappingConfigLoader:
    """YAML 설정 파일을 로드하고 처리하는 클래스"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """매핑 설정 로더 초기화
        
        Args:
            logger: 로거 인스턴스. 기본값은 None
        """
        self.config_path = os.path.join(
            os.path.dirname(__file__),
            "mapping_config.yaml"
        )
        self.logger = logger or logging.getLogger(__name__)
        self.config = self._load_config()
        self.logger.info("Initialized MappingConfigLoader with config path: %s", self.config_path)
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.info("Successfully loaded mapping configuration")
            return config
        except Exception as e:
            self.logger.error("Error loading mapping configuration: %s", str(e), exc_info=True)
            raise
    
    def get_document_type_mapping(self) -> Dict[str, list]:
        """문서 타입 매핑 설정 반환"""
        try:
            mapping = self.config.get('document_types', {}).get('mapping', {})
            self.logger.debug("Retrieved document type mapping: %s", mapping)
            return mapping
        except Exception as e:
            self.logger.error("Error getting document type mapping: %s", str(e), exc_info=True)
            return {}
    
    def get_metadata_mapping(self) -> Dict[str, str]:
        """메타데이터 매핑 설정 반환"""
        try:
            mapping = self.config.get('metadata', {}).get('fields', {})
            self.logger.debug("Retrieved metadata mapping: %s", mapping)
            return mapping
        except Exception as e:
            self.logger.error("Error getting metadata mapping: %s", str(e), exc_info=True)
            return {}
    
    def get_supplier_info_mapping(self) -> Dict[str, str]:
        """공급업체 정보 매핑 설정 반환"""
        try:
            mapping = self.config.get('supplier_info', {}).get('fields', {})
            self.logger.debug("Retrieved supplier info mapping: %s", mapping)
            return mapping
        except Exception as e:
            self.logger.error("Error getting supplier info mapping: %s", str(e), exc_info=True)
            return {}
    
    def get_meeting_info_mapping(self) -> Dict[str, str]:
        """회의 정보 매핑 설정 반환"""
        try:
            mapping = self.config.get('meeting_info', {}).get('fields', {})
            self.logger.debug("Retrieved meeting info mapping: %s", mapping)
            return mapping
        except Exception as e:
            self.logger.error("Error getting meeting info mapping: %s", str(e), exc_info=True)
            return {}
    
    def get_internal_participants_mapping(self) -> Dict[str, Any]:
        """내부 참석자 매핑 설정 반환"""
        try:
            mapping = self.config.get('internal_participants', {})
            self.logger.debug("Retrieved internal participants mapping: %s", mapping)
            return mapping
        except Exception as e:
            self.logger.error("Error getting internal participants mapping: %s", str(e), exc_info=True)
            return {}
    
    def get_external_participants_mapping(self) -> Dict[str, Any]:
        """외부 참석자 매핑 설정 반환"""
        try:
            mapping = self.config.get('external_participants', {})
            self.logger.debug("Retrieved external participants mapping: %s", mapping)
            return mapping
        except Exception as e:
            self.logger.error("Error getting external participants mapping: %s", str(e), exc_info=True)
            return {}
    
    def get_items_mapping(self) -> Dict[str, Any]:
        """품목 매핑 설정 반환"""
        try:
            mapping = self.config.get('items', {})
            self.logger.debug("Retrieved items mapping: %s", mapping)
            return mapping
        except Exception as e:
            self.logger.error("Error getting items mapping: %s", str(e), exc_info=True)
            return {}
    
    def get_nested_value(self, data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """중첩된 딕셔너리에서 값을 추출
        
        Args:
            data: 중첩된 딕셔너리
            path: 점(.)으로 구분된 경로
            default: 기본값
            
        Returns:
            추출된 값 또는 기본값
        """
        try:
            current = data
            for key in path.split("."):
                if isinstance(current, dict):
                    current = current.get(key, default)
                elif isinstance(current, list):
                    if key.isdigit():
                        current = current[int(key)] if int(key) < len(current) else default
                    else:
                        current = [item.get(key, default) for item in current]
                else:
                    return default
            return current
        except Exception as e:
            self.logger.error("Error getting nested value for path %s: %s", path, str(e), exc_info=True)
            return default 