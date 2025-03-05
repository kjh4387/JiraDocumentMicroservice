from typing import Dict, Any, List
from app.source.core.logging import get_logger
import copy
import re

logger = get_logger(__name__)

class Preprocessor:
    """전처리기 기본 클래스"""
    
    def preprocess(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """요청 데이터 전처리"""
        raise NotImplementedError("Subclasses must implement this method")

class MarkdownTablePreprocessor(Preprocessor):
    """마크다운 테이블 파싱 전처리기"""
    
    def __init__(self, field_mapping=None):
        # 필드 매핑: {"items_table": {"target": "items", "columns": ["name", "quantity", "unit_price"]}}
        self.field_mapping = field_mapping or {}
        
    def preprocess(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """마크다운 테이블을 파싱하여 구조화된 데이터로 변환"""
        processed_request = copy.deepcopy(request)
        
        if "direct_data" not in processed_request:
            return processed_request
            
        direct_data = processed_request["direct_data"]
        
        # 설정된 필드 매핑 순회
        for source_field, mapping in self.field_mapping.items():
            if source_field in direct_data and isinstance(direct_data[source_field], str):
                target_field = mapping.get("target", source_field)
                columns = mapping.get("columns", [])
                
                # 테이블 파싱
                table_text = direct_data[source_field]
                parsed_data = self._parse_markdown_table(table_text, columns)
                
                if parsed_data:
                    # 파싱된 데이터를 타겟 필드에 저장
                    direct_data[target_field] = parsed_data
                    
                    # 원본 필드 제거 (선택적)
                    if mapping.get("remove_source", True):
                        direct_data.pop(source_field)
        
        return processed_request
    
    def _parse_markdown_table(self, table_text: str, column_names: List[str] = None) -> List[Dict[str, Any]]:
        """마크다운 테이블 파싱"""
        if not table_text.strip():
            return []
            
        lines = table_text.strip().split('\n')
        if len(lines) < 3:  # 헤더 + 구분선 + 최소 1개 데이터 필요
            logger.warning(f"Invalid markdown table format: too few lines")
            return []
            
        # 헤더 파싱 (컬럼명 추출)
        header_line = lines[0].strip()
        if not header_line.startswith('|'):
            logger.warning(f"Invalid markdown table header: missing pipe")
            return []
            
        # '|' 로 분리하고 공백 제거, 빈 문자열 제거
        headers = [h.strip() for h in header_line.strip('|').split('|')]
        headers = [h for h in headers if h]  # 빈 문자열 제거
        
        # 구분선 검증
        separator_line = lines[1].strip()
        if not separator_line.startswith('|') or not all('-' in cell for cell in separator_line.strip('|').split('|')):
            logger.warning(f"Invalid markdown table: separator line incorrect")
            return []
            
        # 사용자 지정 컬럼명이 있으면 사용
        if column_names and len(column_names) == len(headers):
            headers = column_names
            
        # 데이터 행 파싱
        items = []
        for i, line in enumerate(lines[2:], start=2):  # 헤더와 구분선 이후부터
            if not line.strip() or not '|' in line:
                continue
                
            # '|' 로 분리하고 공백 제거
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            cells = [cell for cell in cells if cell != '']  # 빈 문자열 제거
            
            if len(cells) != len(headers):
                logger.warning(f"Row {i+1} has different number of cells than headers")
                continue
                
            # 셀 데이터로 딕셔너리 생성
            item = {}
            for j, header in enumerate(headers):
                if j < len(cells):
                    # 숫자 값 자동 변환 (정수/실수)
                    cell_value = cells[j]
                    if re.match(r'^-?\d+$', cell_value):
                        item[header] = int(cell_value)
                    elif re.match(r'^-?\d+\.\d+$', cell_value):
                        item[header] = float(cell_value)
                    else:
                        item[header] = cell_value
            
            items.append(item)
                
        return items 