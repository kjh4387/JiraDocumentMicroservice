from typing import Dict, Any
import logging
import sys
import json
from datetime import datetime
from app.source.core.interfaces import Logger

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class JsonFormatter(logging.Formatter):
    """JSON 형식의 로그 포맷터"""
    
    def _build_log_record(self, record):
        """로그 레코드를 JSON 형식으로 변환"""
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 추가 정보가 있으면 포함
        if hasattr(record, "data") and record.data:
            log_record["data"] = record.data
        
        return log_record
    
    def format(self, record):
        log_record = self._build_log_record(record)
        return json.dumps(log_record, cls=DateTimeEncoder)

class ApplicationLogger(Logger):
    """애플리케이션 로거 구현"""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(console_handler)
    
    def _log(self, level: int, message: str, **kwargs):
        """로그 기록"""
        extra = {"data": kwargs} if kwargs else None
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """정보 로그"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """경고 로그"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """오류 로그"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """심각한 오류 로그"""
        self._log(logging.CRITICAL, message, **kwargs)

def get_logger(name: str) -> Logger:
    """로거 인스턴스 반환"""
    return ApplicationLogger(name)
