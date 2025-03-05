import os
import sys
import unittest
import tempfile
import shutil
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, project_root)

# 상대 경로 임포트 사용
from app.source.config.di_container import DIContainer
from app.source.core.domain import Company, Employee, Research

class TestDocumentFlow(unittest.TestCase):
    """문서 생성 흐름 통합 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # 임시 디렉토리 생성
        cls.temp_dir = tempfile.mkdtemp()
        cls.output_dir = os.path.join(cls.temp_dir, "output")
        os.makedirs(cls.output_dir, exist_ok=True)
        
        print(f"\n임시 디렉토리: {cls.temp_dir}")
        print(f"출력 디렉토리: {cls.output_dir}")
        
        # 환경 변수 출력 (디버깅용)
        print(f"DB_HOST: {os.environ.get('DB_HOST')}")
        print(f"DB_PORT: {os.environ.get('DB_PORT')}")
        print(f"DB_USER: {os.environ.get('DB_USER')}")
        print(f"DB_NAME: {os.environ.get('DB_NAME')}")
        
        # 테스트 설정
        cls.config = {
            "schema_path": "app/source/schemas/IntergratedDocumentSchema.json",
            "template_dir": "templates",
            "output_dir": cls.output_dir,
            "database": {
                "host": os.environ.get("DB_HOST", "db"),  # Docker 서비스 이름 사용
                "port": int(os.environ.get("DB_PORT", 5432)),
                "user": os.environ.get("DB_USER", "document_user"),
                "password": os.environ.get("DB_PASSWORD", "document_password"),
                "database": os.environ.get("DB_NAME", "document_db")
            }
        }
        
        # 의존성 주입 컨테이너 초기화
        cls.container = DIContainer(cls.config)
        
        # 기존 테이블 강제 삭제 후 재생성
        from app.source.infrastructure.persistence.db_init import cleanup_database, init_database
        try:
            cleanup_database(cls.container.db_connection)
        except:
            pass  # 테이블이 없어도 무시
        init_database(cls.container.db_connection)
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        # 임시 디렉토리 유지 (주석 처리)
        # shutil.rmtree(cls.temp_dir)
        print(f"\n임시 디렉토리가 유지됩니다: {cls.temp_dir}")
    
    def setUp(self):
        """테스트 설정"""
        # 문서 서비스 가져오기
        self.document_service = self.container.document_service
        
        # 트랜잭션 시작
        self.transaction = self.container.unit_of_work
        self.transaction.__enter__()
        
        # 테스트 데이터 설정
        self.setup_test_data()
    
    def tearDown(self):
        """테스트 정리"""
        # 트랜잭션 롤백 (변경사항 취소)
        self.transaction.rollback()
        self.transaction.__exit__(None, None, None)
        
        # 테스트 데이터 정리 (추가 보장)
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """테스트 데이터 정리"""
        # 테스트에서 생성한 데이터 삭제
        try:
            self.container.company_repo.delete("COMP-TEST-001")
            self.container.employee_repo.delete("EMP-TEST-001")
            self.container.research_repo.delete("PROJ-TEST-001")
        except Exception as e:
            print(f"Error cleaning up test data: {e}")
    
    def setup_test_data(self):
        """테스트 데이터 설정"""
        # 테스트 회사 생성
        company = Company(
            id="COMP-TEST-001",
            company_name="테스트 주식회사",
            biz_id="123-45-67890",
            rep_name="김테스트",
            address="서울시 강남구 테스트로 123",
            biz_type="서비스업",
            biz_item="소프트웨어 개발"
        )
        self.container.company_repo.save(company)
        
        # 테스트 직원 생성
        employee = Employee(
            id="EMP-TEST-001",
            name="홍길동",
            department="개발팀",
            position="팀장",
            email="test@example.com"
        )
        self.container.employee_repo.save(employee)
        
        # 테스트 연구 과제 생성
        research = Research(
            id="PROJ-TEST-001",
            project_name="테스트 프로젝트",
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="홍길동"
        )
        self.container.research_repo.save(research)
    
    def test_create_estimate_document(self):
        """견적서 생성 테스트"""
        # 견적서 데이터
        estimate_data = {
            "document_type": "견적서",
            "metadata": {
                "document_number": "EST-2023-001",
                "date_issued": datetime.now().strftime("%Y-%m-%d"),
                "receiver": "홍길동"
            },
            "supplier_info": {
                "company_id": "COMP-TEST-001"  # 테스트 회사 ID
            },
            "item_list": [
                {
                    "name": "테스트 상품",
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
        self.assertIsNotNone(result)
        self.assertIn("document_id", result)
        self.assertIn("html", result)
        self.assertIn("pdf", result)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "견적서_테스트.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 생성 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)
    
    def test_create_travel_document(self):
        """출장신청서 생성 테스트"""
        # 출장신청서 데이터
        travel_data = {
            "document_type": "출장신청서",
            "research_project_info": {
                "project_id": "PROJ-TEST-001"  # 테스트 연구 과제 ID
            },
            "travel_list": [
                {
                    "employee_id": "EMP-TEST-001",  # 테스트 직원 ID
                    "purpose": "고객사 미팅",
                    "duration": "2023-06-01 ~ 2023-06-03",
                    "destination": "서울"
                }
            ],
            "approval_list": [
                {
                    "employee_id": "EMP-TEST-001",
                    "approval_status": "대기"
                }
            ]
        }
        
        # 문서 생성
        result = self.document_service.create_document(travel_data)
        
        # 검증
        self.assertIsNotNone(result)
        self.assertIn("document_id", result)
        self.assertIn("html", result)
        self.assertIn("pdf", result)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "출장신청서_테스트.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 생성 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)

if __name__ == "__main__":
    unittest.main()
