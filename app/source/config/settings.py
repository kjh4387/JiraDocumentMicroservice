import os
import json
from typing import Dict, Any
from core.exceptions import ConfigurationError
from core.logging import get_logger

logger = get_logger(__name__)

class Settings:
    """애플리케이션 설정 관리"""
    
    def __init__(self, config_path: str = None):
        """설정 초기화"""
        self.config = {}
        
        # 기본 설정
        self._load_default_settings()
        
        # 환경 변수에서 설정 로드
        self._load_from_env()
        
        # 설정 파일에서 로드
        if config_path:
            self._load_from_file(config_path)
        
        # 설정 검증
        self._validate_settings()
        
        logger.info("Settings initialized")
    
    def _load_default_settings(self):
        """기본 설정 로드"""
        self.config = {
            "schema_path": "schemas/IntegratedDocumentSchema.json",
            "template_dir": "templates",
            "output_dir": "output",
            "log_level": "INFO",
            "database": {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "document_db"
            }
        }
        logger.debug("Default settings loaded")
    
    def _load_from_env(self):
        """환경 변수에서 설정 로드"""
        # 데이터베이스 설정
        if os.environ.get("DB_HOST"):
            self.config["database"]["host"] = os.environ.get("DB_HOST")
        if os.environ.get("DB_PORT"):
            self.config["database"]["port"] = int(os.environ.get("DB_PORT", 5432))
        if os.environ.get("DB_USER"):
            self.config["database"]["user"] = os.environ.get("DB_USER")
        if os.environ.get("DB_PASSWORD"):
            self.config["database"]["password"] = os.environ.get("DB_PASSWORD")
        if os.environ.get("DB_NAME"):
            self.config["database"]["database"] = os.environ.get("DB_NAME")
        
        # 기타 설정
        if os.environ.get("SCHEMA_PATH"):
            self.config["schema_path"] = os.environ.get("SCHEMA_PATH")
        
        if os.environ.get("TEMPLATE_DIR"):
            self.config["template_dir"] = os.environ.get("TEMPLATE_DIR")
        
        if os.environ.get("OUTPUT_DIR"):
            self.config["output_dir"] = os.environ.get("OUTPUT_DIR")
        
        if os.environ.get("LOG_LEVEL"):
            self.config["log_level"] = os.environ.get("LOG_LEVEL")
        
        logger.debug("Settings loaded from environment variables")
    
    def _load_from_file(self, config_path: str):
        """설정 파일에서 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                
                # 설정 병합
                self._merge_config(file_config)
                
            logger.debug("Settings loaded from file", config_path=config_path)
        except Exception as e:
            logger.error("Failed to load settings from file", config_path=config_path, error=str(e))
            raise ConfigurationError(f"Failed to load settings from {config_path}: {str(e)}")
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """설정 병합"""
        for key, value in new_config.items():
            if isinstance(value, dict) and key in self.config and isinstance(self.config[key], dict):
                # 중첩된 딕셔너리는 재귀적으로 병합
                for sub_key, sub_value in value.items():
                    self.config[key][sub_key] = sub_value
            else:
                # 일반 값은 덮어쓰기
                self.config[key] = value
    
    def _validate_settings(self):
        """설정 검증"""
        # 필수 설정 확인
        required_settings = ["schema_path", "template_dir", "output_dir", "database"]
        for setting in required_settings:
            if setting not in self.config:
                logger.error(f"Missing required setting: {setting}")
                raise ConfigurationError(f"Missing required setting: {setting}")
        
        # 데이터베이스 설정 확인
        required_db_settings = ["host", "user", "database"]
        for setting in required_db_settings:
            if setting not in self.config["database"]:
                logger.error(f"Missing required database setting: {setting}")
                raise ConfigurationError(f"Missing required database setting: {setting}")
        
        # 파일 경로 확인
        if not os.path.exists(self.config["schema_path"]):
            logger.warning(f"Schema file not found: {self.config['schema_path']}")
        
        if not os.path.exists(self.config["template_dir"]):
            logger.warning(f"Template directory not found: {self.config['template_dir']}")
            # 템플릿 디렉토리 생성
            os.makedirs(self.config["template_dir"], exist_ok=True)
            logger.info(f"Created template directory: {self.config['template_dir']}")
        
        # 출력 디렉토리 생성
        os.makedirs(self.config["output_dir"], exist_ok=True)
        logger.debug(f"Ensured output directory exists: {self.config['output_dir']}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
        return self.config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """설정 값 가져오기 (딕셔너리 스타일)"""
        return self.config[key]
    
    def __contains__(self, key: str) -> bool:
        """설정 키 존재 여부 확인"""
        return key in self.config

def get_settings(config_path: str = None) -> Settings:
    """설정 인스턴스 반환"""
    return Settings(config_path)
