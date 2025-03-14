import re
from typing import Dict, Any, List, Optional, TypedDict, Union
import json
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class TableColumn(TypedDict):
    name: str
    key: str
    type: str

class JiraPreprocessor:
    """Jira에서 전달받은 데이터를 전처리하는 클래스"""
    
    def __init__(self, schema_validator=None):
        """초기화"""
        self.schema_validator = schema_validator
        # 각 문서 유형에 따른 마크다운 테이블 필드 매핑
        self.table_field_mapping = {
            "견적서": {
                "item_list": [
                    {"name": "품명", "key": "name", "type": "str"},
                    {"name": "규격", "key": "spec", "type": "str"},
                    {"name": "수량", "key": "quantity", "type": "int"},
                    {"name": "단가", "key": "unit_price", "type": "int"},
                ]
            },
            "거래명세서": {
                "item_list": [
                    {"name": "품명", "key": "name", "type": "str"},
                    {"name": "규격", "key": "spec", "type": "str"},
                    {"name": "수량", "key": "quantity", "type": "int"},
                    {"name": "단가", "key": "unit_price", "type": "int"},
                ]
            },
            "출장정산신청서": {
                "expense_list": [
                    {"name": "날짜", "key": "date", "type": "str"},
                    {"name": "항목", "key": "category", "type": "str"},
                    {"name": "내용", "key": "detail", "type": "str"},
                    {"name": "금액", "key": "amount", "type": "int"},
                    {"name": "증빙", "key": "receipt", "type": "str"}
                ]
            },
            "구매의뢰서": {
                "item_list": [
                    {"name": "품명", "key": "name", "type": "str"},
                    {"name": "규격", "key": "spec", "type": "str"},
                    {"name": "수량", "key": "quantity", "type": "int"},
                    {"name": "단가", "key": "unit_price", "type": "int"},
                    {"name": "용도", "key": "purpose", "type": "str"}
                ]
            },
            "지출결의서": {
                "expense_list": [
                    {"name": "항목명", "key": "item_name", "type": "str"},
                    {"name": "금액", "key": "amount", "type": "int"},
                    {"name": "비고", "key": "memo", "type": "str"}
                ]
            }
        }
        
        logger.debug("JiraPreprocessor initialized")
    
    def preprocess(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Jira 데이터 전처리
        
        Args:
            data (Dict[str, Any]): Jira로부터 받은 원본 데이터
            
        Returns:
            Dict[str, Any]: 전처리된 데이터
        """
        logger.debug("Starting data preprocessing")
        
        # 데이터 복사
        processed_data = data.copy()
        
        # 문서 유형 확인
        document_type = processed_data.get("document_type", "")
        if not document_type:
            logger.error("Document type not found in data")
            return processed_data
        
        # 문서 유형에 맞는 테이블 필드 매핑 가져오기
        mapping = self.table_field_mapping.get(document_type, {})
        if not mapping:
            logger.debug(f"No table field mapping for document type: {document_type}")
            return processed_data
        
        # 각 필드별 처리
        for field_name, column_info in mapping.items():
            # 해당 필드가 있고 문자열 형태인지 확인
            if field_name in processed_data and isinstance(processed_data[field_name], str):
                table_text = processed_data[field_name]
                # 마크다운 테이블을 리스트로 파싱
                try:
                    parsed_list = self._parse_markdown_table(table_text, column_info)
                    if parsed_list:
                        processed_data[field_name] = parsed_list
                        logger.debug(f"Successfully parsed markdown table for field: {field_name}")
                    else:
                        logger.warning(f"Failed to parse markdown table for field: {field_name}")
                except Exception as e:
                    logger.error(f"Error parsing table for field {field_name}: {str(e)}")
        
        return processed_data
    
    def _parse_markdown_table(self, table_text: str, column_info: List[TableColumn]) -> List[Dict[str, Any]]:
        """마크다운 테이블을 리스트로 파싱
        
        Args:
            table_text (str): 마크다운 테이블 텍스트
            column_info (List[Dict]): 컬럼 정보
            
        Returns:
            List[Dict[str, Any]]: 파싱된 리스트
        """
        # 결과 리스트
        result = []
        
        # 빈 테이블이면 빈 리스트 반환
        if not table_text or table_text.strip() == "":
            return result
        
        # 테이블 줄 분리
        lines = table_text.strip().split('\n')
        
        # 줄이 최소 3개 이상이어야 함 (헤더, 구분선, 데이터 최소 1줄)
        if len(lines) < 3:
            logger.warning("Table has less than 3 lines, not a valid markdown table")
            return result
        
        # 헤더 행과 구분선 확인
        header_line = lines[0]
        separator_line = lines[1]
        
        # 테이블 구문 확인 (최소한 | 문자가 있어야 함)
        if '|' not in header_line or '|' not in separator_line:
            logger.warning("Table format is invalid, missing '|' characters")
            return result
        
        # 헤더 파싱
        headers = [col.strip() for col in header_line.split('|') if col.strip()]
        
        # 헤더와 컬럼 정보의 매핑 확인
        header_to_key = {}
        for col_info in column_info:
            if col_info["name"] in headers:
                header_to_key[col_info["name"]] = {
                    "key": col_info["key"],
                    "type": col_info["type"]
                }
            else:
                logger.warning(f"Column '{col_info['name']}' not found in table headers")
        
        # 데이터 행 처리
        for line_idx in range(2, len(lines)):
            line = lines[line_idx]
            if not line.strip() or '|' not in line:
                continue
                
            # 행 데이터 파싱
            values = [val.strip() for val in line.split('|') if val.strip() != ""]
            
            # 헤더 수와 값 수가 맞는지 확인
            if len(headers) != len(values):
                logger.warning(f"Header and value count mismatch in line {line_idx+1}. Headers: {len(headers)}, Values: {len(values)}")
                continue
            
            # 행 데이터 객체 생성
            row_data = {}
            for i, header in enumerate(headers):
                if i < len(values) and header in header_to_key:
                    col_key = header_to_key[header]["key"]
                    col_type = header_to_key[header]["type"]
                    
                    # 값 타입 변환
                    try:
                        if col_type == "int":
                            # 금액 형식(1,000,000) 처리
                            clean_value = values[i].replace(",", "")
                            row_data[col_key] = int(clean_value)
                        elif col_type == "float":
                            row_data[col_key] = float(values[i])
                        elif col_type == "bool":
                            row_data[col_key] = values[i].lower() in ("true", "yes", "y", "1")
                        else:  # str 등 다른 타입
                            row_data[col_key] = values[i]
                    except ValueError:
                        logger.warning(f"Type conversion error for column {header}, value: {values[i]}")
                        row_data[col_key] = values[i]  # 원본 값으로 저장
            
            # 결과에 행 데이터 추가
            if row_data:
                result.append(row_data)
        
        return result
    
    def calculate_amount_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """항목 리스트에서 금액 합계 계산
        
        Args:
            data (Dict[str, Any]): 전처리된 데이터
            
        Returns:
            Dict[str, Any]: 금액 합계가 추가된 데이터
        """
        document_type = data.get("document_type", "")
        
        # 견적서, 거래명세서, 구매의뢰서일 경우
        if document_type in ["견적서", "거래명세서", "구매의뢰서"]:
            item_list = data.get("item_list", [])
            if item_list and isinstance(item_list, list):
                supply_sum = sum(item.get("amount", 0) for item in item_list)
                vat_sum = sum(item.get("vat", 0) for item in item_list)
                
                # VAT 필드가 없는 경우 10% 자동 계산
                if vat_sum == 0:
                    vat_sum = int(supply_sum * 0.1)
                
                grand_total = supply_sum + vat_sum
                
                data["amount_summary"] = {
                    "supply_sum": supply_sum,
                    "vat_sum": vat_sum,
                    "grand_total": grand_total
                }
        
        # 출장정산신청서
        elif document_type == "출장정산신청서":
            expense_list = data.get("expense_list", [])
            if expense_list and isinstance(expense_list, list):
                total_expense = sum(item.get("amount", 0) for item in expense_list)
                advance_payment = data.get("amount_summary", {}).get("advance_payment", 0)
                
                data["amount_summary"] = {
                    "advance_payment": advance_payment,
                    "total_expense": total_expense,
                    "balance": advance_payment - total_expense
                }
        
        # 지출결의서
        elif document_type == "지출결의서":
            expense_list = data.get("expense_list", [])
            if expense_list and isinstance(expense_list, list):
                grand_total = sum(item.get("amount", 0) for item in expense_list)
                
                data["amount_summary"] = {
                    "grand_total": grand_total
                }
        
        return data 