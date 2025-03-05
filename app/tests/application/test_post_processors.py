import unittest
from unittest.mock import MagicMock
from app.source.application.services.post_processors import (
    DocumentNumberGenerator, ItemAmountCalculator, 
    TotalAmountCalculator, TaxCalculator
)
from datetime import datetime

class TestDocumentNumberGenerator(unittest.TestCase):
    
    def setUp(self):
        self.counter_service = MagicMock()
        self.counter_service.get_next_counter.return_value = 42
        self.processor = DocumentNumberGenerator(self.counter_service)
    
    def test_process_document_number(self):
        current_year = datetime.now().year
        
        data = {
            "document_type": "견적서"
        }
        
        result = self.processor.process(data)
        
        # 현재 연도를 동적으로 사용
        expected_number = f"EST-{current_year}-042"
        self.assertEqual(result["document_number"], expected_number)
        
        # 카운터 서비스가 호출되었는지 확인
        self.counter_service.get_next_counter.assert_called_once()
    
    def test_skip_existing_document_number(self):
        data = {
            "document_type": "견적서",
            "document_number": "EXISTING-001"
        }
        
        result = self.processor.process(data)
        
        # 기존 문서 번호가 유지되는지 확인
        self.assertEqual(result["document_number"], "EXISTING-001")
        
        # 카운터 서비스가 호출되지 않았는지 확인
        self.counter_service.get_next_counter.assert_not_called()

class TestItemAmountCalculator(unittest.TestCase):
    
    def setUp(self):
        self.processor = ItemAmountCalculator()
    
    def test_calculate_item_amounts(self):
        data = {
            "items": [
                {"name": "항목1", "quantity": 2, "unit_price": 1000},
                {"name": "항목2", "quantity": 3, "unit_price": 1500},
                {"name": "항목3", "quantity": "4", "unit_price": "2000"}
            ]
        }
        
        result = self.processor.process(data)
        
        # 각 항목의 금액이 계산되었는지 확인
        self.assertEqual(result["items"][0]["amount"], 2000)  # 2 * 1000
        self.assertEqual(result["items"][1]["amount"], 4500)  # 3 * 1500
        self.assertEqual(result["items"][2]["amount"], 8000)  # 4 * 2000
    
    def test_skip_existing_amounts(self):
        data = {
            "items": [
                {"name": "항목1", "quantity": 2, "unit_price": 1000, "amount": 9999}
            ]
        }
        
        result = self.processor.process(data)
        
        # 기존 금액이 유지되는지 확인
        self.assertEqual(result["items"][0]["amount"], 9999)

class TestTotalAmountCalculator(unittest.TestCase):
    
    def setUp(self):
        self.processor = TotalAmountCalculator()
    
    def test_calculate_total_amount(self):
        data = {
            "items": [
                {"name": "항목1", "amount": 2000},
                {"name": "항목2", "amount": 3000},
                {"name": "항목3", "amount": 5000}
            ]
        }
        
        result = self.processor.process(data)
        
        # 총액이 계산되었는지 확인
        self.assertIn("amounts", result)
        self.assertEqual(result["amounts"]["subtotal"], 10000)  # 2000 + 3000 + 5000
        
        # 한글 금액이 변환되었는지 확인
        self.assertIn("total_in_words", result["amounts"])
        self.assertEqual(result["amounts"]["total_in_words"], "일만원정") 