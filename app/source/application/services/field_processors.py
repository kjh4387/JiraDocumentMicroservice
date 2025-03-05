from typing import Dict, Any, Optional, List
from app.source.core.logging import get_logger
from datetime import datetime
import re

logger = get_logger(__name__)

class FieldProcessor:
    """필드 처리기 기본 클래스"""
    
    def process(self, value: Any, field_spec: Dict[str, Any]) -> Any:
        """필드 값 처리"""
        raise NotImplementedError("Subclasses must implement this method")

class StringFieldProcessor(FieldProcessor):
    """문자열 필드 처리기"""
    
    def process(self, value: Any, field_spec: Dict[str, Any]) -> str:
        # 문자열로 변환
        if not isinstance(value, str):
            value = str(value)
        
        # 최대 길이 검증
        max_length = field_spec.get("max_length")
        if max_length and len(value) > max_length:
            logger.warning(f"String value exceeds max length", 
                          max_length=max_length, 
                          actual_length=len(value))
            value = value[:max_length]
        
        # 선택 목록 검증
        choices = field_spec.get("choices")
        if choices and value not in choices:
            logger.warning(f"Invalid value", value=value, choices=choices)
            if field_spec.get("default") is not None:
                return field_spec.get("default")
        
        return value

class NumberFieldProcessor(FieldProcessor):
    """숫자 필드 처리기"""
    
    def process(self, value: Any, field_spec: Dict[str, Any]) -> float:
        try:
            # 콤마 제거 후 숫자로 변환
            if isinstance(value, str):
                value = value.replace(',', '')
            
            num_value = float(value)
            
            # 최소값 검증
            min_value = field_spec.get("min_value")
            if min_value is not None and num_value < min_value:
                logger.warning(f"Value below minimum", value=num_value, min_value=min_value)
                num_value = min_value
            
            # 최대값 검증
            max_value = field_spec.get("max_value")
            if max_value is not None and num_value > max_value:
                logger.warning(f"Value above maximum", value=num_value, max_value=max_value)
                num_value = max_value
            
            # 정수로 변환이 필요한 경우
            if field_spec.get("integer", False):
                num_value = int(num_value)
            
            return num_value
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid number value", value=value, error=str(e))
            return field_spec.get("default", 0)

class DateFieldProcessor(FieldProcessor):
    """날짜 필드 처리기"""
    
    def process(self, value: Any, field_spec: Dict[str, Any]) -> Dict[str, Any]:
        format_str = field_spec.get("format", "%Y-%m-%d")
        
        try:
            if isinstance(value, str):
                # 날짜 파싱
                dt = datetime.strptime(value, format_str)
                
                # 결과 포맷
                return {
                    "value": value,
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "formatted": dt.strftime(format_str)
                }
            else:
                logger.warning(f"Invalid date format", value=value)
                return {"value": value}
                
        except ValueError as e:
            logger.error(f"Date parsing error", value=value, format=format_str, error=str(e))
            return {"value": value, "error": "Invalid date format"}

class DateRangeFieldProcessor(FieldProcessor):
    """날짜 범위 필드 처리기"""
    
    def process(self, value: Any, field_spec: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(value, str):
            logger.warning(f"Invalid date range format", value=value)
            return {"value": value}
        
        # "2023-12-15 ~ 2023-12-17" 형식 파싱
        pattern = r"(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})"
        match = re.match(pattern, value)
        
        if not match:
            logger.warning(f"Invalid date range pattern", value=value)
            return {"value": value}
            
        start_date = match.group(1)
        end_date = match.group(2)
        
        try:
            # 날짜 유효성 검증
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # 종료일이 시작일보다 이전인지 검증
            if end_dt < start_dt:
                logger.warning(f"End date before start date", 
                              start_date=start_date, 
                              end_date=end_date)
            
            # 결과 포맷
            return {
                "value": value,
                "start_date": start_date,
                "end_date": end_date,
                "formatted": value
            }
                
        except ValueError as e:
            logger.error(f"Date range parsing error", 
                        value=value, 
                        error=str(e))
            return {"value": value, "error": "Invalid date format"}

class ArrayFieldProcessor(FieldProcessor):
    """배열 필드 처리기"""
    
    def process(self, value: Any, field_spec: Dict[str, Any]) -> List[Any]:
        if not isinstance(value, list):
            logger.warning(f"Expected array, got {type(value)}")
            return []
        
        item_spec = field_spec.get("items", {})
        item_processor = self._get_item_processor(item_spec.get("type", "string"))
        
        processed_items = []
        for item in value:
            processed_item = item_processor.process(item, item_spec)
            processed_items.append(processed_item)
            
        return processed_items
    
    def _get_item_processor(self, item_type: str) -> FieldProcessor:
        """항목 타입에 맞는 처리기 반환"""
        processors = {
            "string": StringFieldProcessor(),
            "number": NumberFieldProcessor(),
            "date": DateFieldProcessor(),
            # 기타 필요한 처리기...
        }
        
        return processors.get(item_type, StringFieldProcessor()) 