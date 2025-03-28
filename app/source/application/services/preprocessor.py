import re
from typing import Dict, Any, List, Optional, TypedDict, Union
import json
from app.source.infrastructure.mapping.markdown_parser import MarkdownTableParser
import logging

class TableColumn(TypedDict):
    name: str
    key: str
    type: str

class JiraPreprocessor:
    """Jira에서 전달받은 데이터를 전처리하는 클래스"""
    
    def __init__(self, schema_validator=None):
        """초기화"""
        self.schema_validator = schema_validator
        self.markdown_parser = MarkdownTableParser()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("JiraPreprocessor initialized")
    
    def preprocess(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Jira 데이터 전처리 - 모든 필드에 대해 마크다운 테이블 파싱 시도
        
        Args:
            data (Dict[str, Any]): Jira로부터 받은 원본 데이터
            
        Returns:
            Dict[str, Any]: 전처리된 데이터
        """
        self.logger.info("=== Starting data preprocessing ===")
        
        # 입력 데이터 로깅
        if data is None:
            self.logger.warning("Input data is None")
            return {}
            
        self.logger.debug(f"Input data has {len(data)} top-level keys: {list(data.keys())}")
        if 'fields' in data:
            self.logger.debug(f"Input 'fields' has {len(data['fields'])} keys: {list(data['fields'].keys())}")
        
        # 데이터 복사
        processed_data = data.copy()
        
        # fields 객체 가져오기
        if 'fields' in processed_data:
            self.logger.debug("Processing 'fields' object")
            fields = processed_data['fields']
            # fields 내의 모든 필드 처리 - 필드 목록을 미리 복사
            field_items = list(fields.items())
            markdown_field_count = 0
            for field_name, field_value in field_items:
                if isinstance(field_value, str):
                    self.logger.debug(f"Checking if field '{field_name}' contains markdown table (length: {len(field_value)})")
                    if self._looks_like_markdown_table(field_value):
                        self.logger.debug(f"Field '{field_name}' looks like a markdown table")
                        try:
                            parsed_table = self.markdown_parser.parse_table(field_value)
                            if parsed_table:
                                self.logger.debug(f"Successfully parsed markdown table for '{field_name}': {len(parsed_table)} rows")
                                # 파싱된 결과를 원래 필드_data에 삽입
                                fields[f"{field_name}_data"] = parsed_table
                                self.logger.info(f"Created '{field_name}_data' with {len(parsed_table)} items")
                                markdown_field_count += 1
                                
                                # 첫 번째 행 로깅 (디버깅용)
                                if parsed_table and len(parsed_table) > 0:
                                    self.logger.debug(f"First row of '{field_name}_data': {parsed_table[0]}")
                            else:
                                self.logger.warning(f"Parser returned empty result for '{field_name}' despite looking like a table")
                        except Exception as e:
                            self.logger.error(f"Error parsing markdown table for field '{field_name}': {str(e)}", exc_info=True)
                if field_name == "연구과제_선택":
                    value = field_value["value"]
                    self.logger.debug(f"Field '{field_name}' value: {value}")
                    if value:
                        # 괄호 안의 키를 추출
                        match = re.search(r'\(([^)]+)\)', value)
                        if match:
                            key = match.group(1)
                            self.logger.debug(f"Extracted key: {key}")
                        fields[f"연구과제_선택_key"] = key
                        self.logger.debug(f"Added '{field_name}_key' with value: {key}")
                

            self.logger.info(f"Processed {markdown_field_count} markdown tables in 'fields' object")
        
        # fields 외의 최상위 필드 처리 - 필드 목록을 미리 복사
        self.logger.debug("Processing top-level fields")
        top_level_items = list(processed_data.items())
        top_level_markdown_count = 0
        for field_name, field_value in top_level_items:
            if field_name != 'fields' and isinstance(field_value, str):
                self.logger.debug(f"Checking if top-level field '{field_name}' contains markdown table (length: {len(field_value)})")
                if self._looks_like_markdown_table(field_value):
                    self.logger.debug(f"Top-level field '{field_name}' looks like a markdown table")
                    try:
                        parsed_table = self.markdown_parser.parse_table(field_value)
                        if parsed_table:
                            self.logger.debug(f"Successfully parsed top-level markdown table for '{field_name}': {len(parsed_table)} rows")
                            # 원본 필드를 덮어쓰기 대신 새 필드로 저장
                            processed_data[f"{field_name}_data"] = parsed_table
                            self.logger.info(f"Created top-level '{field_name}_data' with {len(parsed_table)} items")
                            top_level_markdown_count += 1
                            
                            # 첫 번째 행 로깅 (디버깅용)
                            if parsed_table and len(parsed_table) > 0:
                                self.logger.debug(f"First row of top-level '{field_name}_data': {parsed_table[0]}")
                        else:
                            self.logger.warning(f"Parser returned empty result for top-level '{field_name}' despite looking like a table")
                    except Exception as e:
                        self.logger.error(f"Error parsing top-level markdown table for field '{field_name}': {str(e)}", exc_info=True)
        
        self.logger.info(f"Processed {top_level_markdown_count} markdown tables in top-level fields")
        
        # 수량*단가 계산 필드 추가 (item_list_data 필드가 있는 경우)
        self.logger.debug("Checking for item list to calculate amounts")
        if 'fields' in processed_data and 'item_list_data' in processed_data['fields']:
            self.logger.debug("Found 'item_list_data' in fields, calculating amounts")
            self._calculate_item_amounts(processed_data['fields']['item_list_data'])
        elif 'item_list_data' in processed_data:
            self.logger.debug("Found 'item_list_data' at top level, calculating amounts")
            self._calculate_item_amounts(processed_data['item_list_data'])
        else:
            self.logger.debug("No 'item_list_data' found to calculate amounts")
        
        # 금액 합계 계산 (모든 문서 유형에 대해 공통으로 처리)
        self.logger.debug("Calculating amount summary")
        processed_data = self.calculate_amount_summary(processed_data)
        
        # 결과 데이터 로깅
        self.logger.debug(f"After preprocessing, data has {len(processed_data)} top-level keys: {list(processed_data.keys())}")
        if 'fields' in processed_data:
            self.logger.debug(f"After preprocessing, 'fields' has {len(processed_data['fields'])} keys: {list(processed_data['fields'].keys())}")
        
        # 새로 추가된 필드 로깅
        new_fields = [k for k in processed_data.keys() if k not in data.keys()]
        if new_fields:
            self.logger.info(f"Added {len(new_fields)} new top-level fields: {new_fields}")
        
        if 'fields' in processed_data and 'fields' in data:
            new_nested_fields = [k for k in processed_data['fields'].keys() if k not in data['fields'].keys()]
            if new_nested_fields:
                self.logger.info(f"Added {len(new_nested_fields)} new fields in 'fields': {new_nested_fields}")
        
        self.logger.info("=== Data preprocessing completed ===")
        return processed_data
    
    def _looks_like_markdown_table(self, text: str) -> bool:
        """문자열이 마크다운 테이블인지 확인
        
        Args:
            text (str): 확인할 문자열
            
        Returns:
            bool: 마크다운 테이블인 경우 True
        """
        if not text or not isinstance(text, str):
            return False
            
        lines = text.strip().split('\n')
        
        # 최소 3줄 이상 (헤더, 구분선, 데이터)
        if len(lines) < 3:
            self.logger.debug(f"Text has less than 3 lines ({len(lines)}), not a markdown table")
            return False
            
        # 첫 번째 줄과 두 번째 줄에 | 문자가 있어야 함
        if '|' not in lines[0] or '|' not in lines[1]:
            self.logger.debug("Text missing '|' character in first or second line, not a markdown table")
            return False
            
        
        self.logger.debug(f"Text appears to be a valid markdown table with {len(lines)} lines")
        return True
    
    def _calculate_item_amounts(self, items: List[Dict[str, Any]]) -> None:
        """아이템 리스트에 금액 계산 필드 추가
        
        Args:
            items (List[Dict[str, Any]]): 아이템 리스트
        """
        self.logger.debug(f"Calculating amounts for {len(items)} items")
        calculated_count = 0
        
        for i, item in enumerate(items):
            # quantity와 unit_price 필드가 있는지 확인하고 amount 계산
            quantity = item.get('quantity')
            unit_price = item.get('unit_price')
            
            self.logger.debug(f"Item {i+1}: quantity={quantity}, unit_price={unit_price}")
            
            if quantity is not None and unit_price is not None:
                try:
                    # 문자열인 경우 숫자로 변환
                    if isinstance(quantity, str):
                        quantity = int(quantity.replace(',', ''))
                        self.logger.debug(f"Converted string quantity '{item.get('quantity')}' to {quantity}")
                    if isinstance(unit_price, str):
                        unit_price = int(unit_price.replace(',', ''))
                        self.logger.debug(f"Converted string unit_price '{item.get('unit_price')}' to {unit_price}")
                        
                    item['amount'] = quantity * unit_price
                    self.logger.debug(f"Calculated amount for item {i+1}: {item['amount']}")
                    calculated_count += 1
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Failed to calculate amount for item {i+1}: {str(e)}")
            else:
                self.logger.debug(f"Item {i+1} is missing quantity or unit_price, skipping amount calculation")
        
        self.logger.info(f"Successfully calculated amounts for {calculated_count} out of {len(items)} items")
    
    def calculate_amount_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """금액 합계 계산 - 문서 유형에 관계없이 공통 처리
        
        Args:
            data (Dict[str, Any]): 전처리된 데이터
            
        Returns:
            Dict[str, Any]: 금액 합계가 추가된 데이터
        """
        self.logger.debug("Calculating amount summary")
        
        # 항목 리스트 찾기 (fields 내부 또는 최상위)
        item_list = None
        item_list_source = None
        
        if 'fields' in data:
            if 'item_list_data' in data['fields']:
                item_list = data['fields']['item_list_data']
                item_list_source = "fields.item_list_data"
            elif 'expense_list_data' in data['fields']:
                item_list = data['fields']['expense_list_data']
                item_list_source = "fields.expense_list_data"
        else:
            if 'item_list_data' in data:
                item_list = data['item_list_data']
                item_list_source = "item_list_data"
            elif 'expense_list_data' in data:
                item_list = data['expense_list_data']
                item_list_source = "expense_list_data"
        
        if item_list_source:
            self.logger.debug(f"Found item list source: {item_list_source} with {len(item_list)} items")
        else:
            self.logger.debug("No item list found for amount summary calculation")
            return data
        
        # 항목 리스트가 있으면 금액 합계 계산
        if item_list and isinstance(item_list, list):
            # 합계 계산
            total_amount = 0
            items_with_amount = 0
            
            for i, item in enumerate(item_list):
                # 항목의 금액 필드 (amount 또는 다른 필드)
                amount = 0
                if 'amount' in item:
                    try:
                        if isinstance(item['amount'], str):
                            amount = int(item['amount'].replace(',', ''))
                            self.logger.debug(f"Converted string amount '{item['amount']}' to {amount} for item {i+1}")
                        else:
                            amount = item['amount']
                            
                        total_amount += amount
                        items_with_amount += 1
                        self.logger.debug(f"Added amount {amount} from item {i+1}, running total: {total_amount}")
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Error processing amount for item {i+1}: {str(e)}")
                else:
                    self.logger.debug(f"Item {i+1} has no 'amount' field")
            
            self.logger.info(f"Calculated total amount: {total_amount} from {items_with_amount} items with amount")
            
            # 계산된 합계 저장
            amount_summary = {'total_amount': total_amount}
            
            # 부가세 계산 (10%)
            vat = int(total_amount * 0.1)
            amount_summary['vat'] = vat
            amount_summary['grand_total'] = total_amount + vat
            
            self.logger.debug(f"Amount summary calculated: total={total_amount}, vat={vat}, grand_total={total_amount + vat}")
            
            # 데이터에 저장
            if 'fields' in data:
                data['fields']['amount_summary'] = amount_summary
                self.logger.info("Added amount_summary to fields")
            else:
                data['amount_summary'] = amount_summary
                self.logger.info("Added amount_summary to top level")
        
        return data 