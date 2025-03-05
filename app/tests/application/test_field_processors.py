import unittest
from datetime import datetime
from app.source.application.services.field_processors import (
    StringFieldProcessor, NumberFieldProcessor, DateFieldProcessor,
    DateRangeFieldProcessor, ArrayFieldProcessor
)

class TestStringFieldProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = StringFieldProcessor()
    
    def test_process_valid_string(self):
        result = self.processor.process("테스트 문자열", {})
        self.assertEqual(result, "테스트 문자열")
    
    def test_process_non_string(self):
        result = self.processor.process(123, {})
        self.assertEqual(result, "123")
    
    def test_process_max_length(self):
        result = self.processor.process("테스트 문자열", {"max_length": 5})
        self.assertEqual(result, "테스트 문")
    
    def test_process_choices(self):
        spec = {"choices": ["옵션1", "옵션2", "옵션3"]}
        
        # 유효한 선택지
        result = self.processor.process("옵션2", spec)
        self.assertEqual(result, "옵션2")
        
        # 유효하지 않은 선택지
        result = self.processor.process("옵션4", spec)
        self.assertEqual(result, "옵션4")  # 유효성 검사만 수행하고 값은 변경하지 않음

class TestNumberFieldProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = NumberFieldProcessor()
    
    def test_process_valid_number(self):
        result = self.processor.process(123, {})
        self.assertEqual(result, 123)
    
    def test_process_string_number(self):
        result = self.processor.process("123", {})
        self.assertEqual(result, 123)
    
    def test_process_float_number(self):
        result = self.processor.process("123.45", {})
        self.assertEqual(result, 123.45)
    
    def test_process_invalid_number(self):
        result = self.processor.process("not a number", {})
        self.assertEqual(result, 0)  # 기본값 반환
    
    def test_process_min_value(self):
        # 최소값 제약 충족
        result = self.processor.process(10, {"min_value": 5})
        self.assertEqual(result, 10)
        
        # 최소값 제약 위반
        result = self.processor.process(3, {"min_value": 5})
        self.assertEqual(result, 5)  # 최소값으로 조정
    
    def test_process_max_value(self):
        # 최대값 제약 충족
        result = self.processor.process(10, {"max_value": 20})
        self.assertEqual(result, 10)
        
        # 최대값 제약 위반
        result = self.processor.process(30, {"max_value": 20})
        self.assertEqual(result, 20)  # 최대값으로 조정

class TestDateFieldProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = DateFieldProcessor()
    
    def test_process_valid_date_string(self):
        result = self.processor.process("2023-01-15", {})
        self.assertEqual(result.get("value") if isinstance(result, dict) else result, "2023-01-15")
    
    def test_process_date_object(self):
        date_obj = datetime(2023, 1, 15)
        result = self.processor.process(date_obj, {})
        self.assertEqual(result.get("value").strftime("%Y-%m-%d") 
                         if isinstance(result, dict) and isinstance(result.get("value"), datetime) 
                         else result, "2023-01-15")
    
    def test_process_invalid_date(self):
        result = self.processor.process("not a date", {})
        self.assertIn("error", result)

class TestArrayFieldProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = ArrayFieldProcessor()
    
    def test_process_valid_array(self):
        items = ["항목1", "항목2", "항목3"]
        result = self.processor.process(items, {})
        self.assertEqual(result, items)
    
    def test_process_non_array(self):
        result = self.processor.process("not an array", {})
        self.assertEqual(result, [])
    
    def test_process_array_with_item_specs(self):
        items = ["1", "2", "3"]
        item_spec = {"type": "number"}
        spec = {"items": item_spec}
        
        result = self.processor.process(items, spec)
        self.assertEqual(result, [1, 2, 3])  # 숫자로 변환된 결과 