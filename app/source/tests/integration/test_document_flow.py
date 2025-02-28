import unittest
import os
import tempfile
import shutil
from config.di_container import DIContainer
from core.exceptions import DocumentAutomationError

class TestDocumentFlow(unittest.TestCase):
    """문서 생성 흐름 통합 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # 임시 디렉토리 생성
        cls.temp_dir = tempfile.mkdtemp()
        cls.output_dir = os.path.join(cls.temp_dir, "output")
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # 테스트 설정
        cls.config = {
            "schema_path": "schemas/IntegratedDocumentSchema.json",
            "template_dir": "templates",
            "output_dir": cls.output_dir,
            "database": {
                "host": os.environ.get("TEST_DB_HOST", "localhost"),
                "user": os.environ.get("TEST_DB_USER", "test_user"),
                "password": os.environ.get("TEST_DB_PASSWORD", "test_password"),
                "database": os.environ.get("TEST_DB_NAME", "test_document_db")
            }
        }
        
        # 의존성 주입 컨테이너 초기화
        cls.container = DIContainer(cls.config)
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        # 임시 디렉토리 삭제
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """테스트 설정"""
        # 문서 서비스 가져오기
        self.document_service = self.container.document_service
        
        # 테스트 데이터 설정
        self.setup_test_data()
    
    def setup_test_data(self):
        """테스트 데이터 설정"""
        # 회사 정보 저장
        company = {
            "id": "COMP-TEST-001",
            "company_name": "통합테스트 주식회사",
            "biz_id": "123-45-67890",
            "rep_name": "김통합",
            "address": "서울시 강남구",
            "biz_type": "서비스업",
            "biz_item": "소프트웨어 개발",
            "phone": "02-1234-5678"
        }
        self.container.company_repo.save(company)
        
        # 직원 정보 저장
        employee = {
            "id": "EMP-TEST-001",
            "name": "이통합",
            "department": "개발팀",
            "position": "선임연구원",
            "email": "test@example.com",
            "phone": "010-1234-5678"
        }
        self.container.employee_repo.save(employee)
        
        # 연구 과제 정보 저장
        research = {
            "id": "PROJ-TEST-001",
            "project_name": "통합테스트 프로젝트",
            "project_period": "2023-01-01 ~ 2023-12-31",
            "project_manager": "박통합"
        }
        self.container.research_repo.save(research)
    
    def test_estimate_document_flow(self):
        """견적서 생성 흐름 테스트"""
        # 테스트 데이터
        estimate_data = {
            "document_type": "견적서",
            "metadata": {
                "document_number": "EST-TEST-001",
                "date_issued": "2023-05-15",
                "receiver": "통합테스트"
            },
            "supplier_info": {
                "company_id": "COMP-TEST-001"
            },
            "item_list": [
                {
                    "name": "통합테스트 상품",
                    "quantity": 2,
                    "unit_price": 50000,
                    "amount": 100000,
                    "vat": 10000
                }
            ],
            "amount_summary": {
                "supply_sum": 100000,
                "vat_sum": 10000,
                "grand_total": 110000
            }
        }
        
        # 문서 생성
        result = self.document_service.create_document(estimate_data)
        
        # 검증
        self.assertEqual(result["document_type"], "견적서")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_estimate.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)
    
    def test_travel_application_document_flow(self):
        """출장신청서 생성 흐름 테스트"""
        # 테스트 데이터
        travel_data = {
            "document_type": "출장신청서",
            "metadata": {
                "document_number": "TRAVEL-TEST-001",
                "date_issued": "2023-05-20"
            },
            "research_project_info": {
                "project_id": "PROJ-TEST-001"
            },
            "travel_list": [
                {
                    "employee_id": "EMP-TEST-001",
                    "purpose": "통합테스트 미팅",
                    "duration": "2023-06-01 ~ 2023-06-03",
                    "destination": "서울"
                }
            ]
        }
        
        # 문서 생성
        result = self.document_service.create_document(travel_data)
        
        # 검증
        self.assertEqual(result["document_type"], "출장신청서")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_travel.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)

if __name__ == '__main__':
    unittest.main()
