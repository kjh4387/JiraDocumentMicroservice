from typing import Dict, Any
from app.source.core.logging import get_logger
from datetime import datetime
import re

logger = get_logger(__name__)

class PostProcessor:
    """후처리기 기본 클래스"""
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 데이터 후처리"""
        raise NotImplementedError("Subclasses must implement this method")

class DocumentNumberGenerator(PostProcessor):
    """문서 번호 생성 후처리기"""
    
    def __init__(self, counter_service):
        self.counter_service = counter_service
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 번호 자동 생성"""
        doc_type = data.get("document_type")
        if not doc_type:
            return data
            
        # 이미 문서 번호가 있으면 스킵
        if "document_number" in data:
            return data
            
        # 문서 유형별 접두사 매핑
        prefix_map = {
            "출장신청서": "TRAVEL",
            "견적서": "EST",
            "전문가활용계획서": "EUP",
            # 기타 문서 유형...
        }
        
        # 접두사 결정 (없으면 문서 유형의 앞 4글자 사용)
        prefix = prefix_map.get(doc_type, doc_type[:4].upper())
        
        # 현재 년도와 일련번호로 문서 번호 생성
        year = datetime.now().year
        counter = self.counter_service.get_next_counter(doc_type, year)
        
        document_number = f"{prefix}-{year}-{counter:03d}"
        data["document_number"] = document_number
        
        return data

class ItemAmountCalculator(PostProcessor):
    """항목별 금액 계산 후처리기"""
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """항목별 금액 자동 계산"""
        if "items" not in data or not isinstance(data["items"], list):
            return data
            
        for item in data["items"]:
            if "quantity" in item and "unit_price" in item and "amount" not in item:
                try:
                    quantity = float(item["quantity"])
                    unit_price = float(item["unit_price"])
                    item["amount"] = int(quantity * unit_price)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid quantity or unit price", 
                                 quantity=item.get("quantity"), 
                                 unit_price=item.get("unit_price"))
        
        return data

class TotalAmountCalculator(PostProcessor):
    """총액 계산 후처리기"""
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """총액 자동 계산"""
        if "items" not in data or not isinstance(data["items"], list):
            return data
            
        # 모든 항목의 금액 합계 계산
        total = 0
        for item in data["items"]:
            if "amount" in item:
                try:
                    total += float(item["amount"])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid amount", amount=item.get("amount"))
        
        # 금액 정보 구조화
        if "amounts" not in data:
            data["amounts"] = {}
            
        data["amounts"]["subtotal"] = int(total)
        
        # 한글 금액으로 변환
        data["amounts"]["total_in_words"] = self._number_to_korean(int(total))
        
        return data
    
    def _number_to_korean(self, number: int) -> str:
        """숫자를 한글 금액으로 변환"""
        if number == 0:
            return "영원"
            
        units = ['', '만', '억', '조']
        nums = ['영', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
        
        result = ''
        i = 0
        while number > 0:
            n = number % 10000
            if n > 0:
                s = ''
                for j in range(4):
                    m = n % 10
                    if m > 0:
                        s = nums[m] + ['', '십', '백', '천'][j] + s
                    n = n // 10
                result = s + units[i] + result
            i += 1
            number = number // 10000
            
        return result + '원정'

class TravelDurationCalculator(PostProcessor):
    """출장 기간 계산 후처리기"""
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """출장 일수 계산"""
        if "travel_period" not in data:
            return data
            
        travel_period = data["travel_period"]
        if not isinstance(travel_period, dict):
            return data
            
        if "start_date" in travel_period and "end_date" in travel_period:
            try:
                start_date = datetime.strptime(travel_period["start_date"], "%Y-%m-%d")
                end_date = datetime.strptime(travel_period["end_date"], "%Y-%m-%d")
                
                # 일수 계산 (같은 날짜면 1일)
                delta = end_date - start_date
                days = delta.days + 1
                
                travel_period["days"] = days
                
                # 업무일수 계산 (주말 제외)
                business_days = 0
                current_date = start_date
                while current_date <= end_date:
                    # 월요일(0) ~ 금요일(4)
                    if current_date.weekday() < 5:
                        business_days += 1
                    current_date = current_date + datetime.timedelta(days=1)
                
                travel_period["business_days"] = business_days
                
            except (ValueError, KeyError) as e:
                logger.error(f"Failed to calculate travel duration", error=str(e))
        
        return data

class TaxCalculator(PostProcessor):
    """세금 계산 후처리기"""
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """부가가치세 계산"""
        if "amounts" not in data or not isinstance(data["amounts"], dict):
            return data
            
        amounts = data["amounts"]
        if "subtotal" in amounts:
            try:
                subtotal = float(amounts["subtotal"])
                
                # 부가세 계산 (10%)
                tax = int(subtotal * 0.1)
                amounts["tax"] = tax
                
                # 총액 계산
                total = int(subtotal + tax)
                amounts["total"] = total
                
                # 한글 금액 업데이트
                if "total_in_words" in amounts:
                    amounts["total_in_words"] = self._number_to_korean(total)
                
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to calculate tax", error=str(e))
        
        return data
    
    def _number_to_korean(self, number: int) -> str:
        """숫자를 한글 금액으로 변환"""
        if number == 0:
            return "영원"
            
        units = ['', '만', '억', '조']
        nums = ['영', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
        
        result = ''
        i = 0
        while number > 0:
            n = number % 10000
            if n > 0:
                s = ''
                for j in range(4):
                    m = n % 10
                    if m > 0:
                        s = nums[m] + ['', '십', '백', '천'][j] + s
                    n = n // 10
                result = s + units[i] + result
            i += 1
            number = number // 10000
            
        return result + '원정' 