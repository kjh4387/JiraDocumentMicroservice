import unittest
import os
import tempfile
import shutil
import psycopg2
from app.source.config.di_container import DIContainer
from app.source.core.exceptions import DocumentAutomationError
# 명시적으로 각 도메인 클래스 임포트
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
        
        # Create absolute path to project root and resources
        # 현재 테스트 파일의 위치를 기준으로 경로 구성
        current_dir = os.path.dirname(os.path.abspath(__file__))
        source_dir = os.path.dirname(os.path.dirname(current_dir))  # app/source 디렉토리
        
        # 테스트 설정
        cls.config = {
            "schema_path": os.path.join(source_dir, "schemas", "IntegratedDocumentSchema.json"),
            "template_dir": os.path.join(source_dir, "templates"),
            "output_dir": cls.output_dir,
            "database": {
                "host": os.environ.get("DB_HOST", "db"),  # Docker 서비스 이름 사용
                "port": int(os.environ.get("DB_PORT", 5432)),  # 포트 명시적 설정
                "user": os.environ.get("DB_USER", "myuser"),
                "password": os.environ.get("DB_PASSWORD", "mypassword"),
                "database": os.environ.get("DB_NAME", "mydb")
            }
        }
        
        # 테스트 데이터베이스에 테이블 생성
        cls._create_test_tables()
        
        # 의존성 주입 컨테이너 초기화
        cls.container = DIContainer(cls.config)
    
    @classmethod
    def _create_test_tables(cls):
        """테스트 테이블 생성"""
        print("Creating test tables...")
        db_config = cls.config["database"]
        
        conn = None
        try:
            # DB 연결
            conn = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                user=db_config["user"],
                password=db_config["password"],
                database=db_config["database"]
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # 회사 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id VARCHAR(50) PRIMARY KEY,
                    company_name VARCHAR(100) NOT NULL,
                    biz_id VARCHAR(20) NOT NULL,
                    rep_name VARCHAR(50) NOT NULL,
                    address VARCHAR(200) NOT NULL,
                    biz_type VARCHAR(50) NOT NULL,
                    biz_item VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    rep_stamp BYTEA
                )
            """)
            
            # 직원 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    department VARCHAR(50) NOT NULL,
                    position VARCHAR(50) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    signature VARCHAR(100),
                    bank_name VARCHAR(50),
                    account_number VARCHAR(50)
                )
            """)
            
            # 연구 과제 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_projects (
                    id VARCHAR(50) PRIMARY KEY,
                    project_name VARCHAR(100) NOT NULL,
                    project_period VARCHAR(50) NOT NULL,
                    project_manager VARCHAR(50) NOT NULL,
                    project_code VARCHAR(50)
                )
            """)
            
            # 기존 데이터 정리
            cursor.execute("DELETE FROM companies")
            cursor.execute("DELETE FROM employees")
            cursor.execute("DELETE FROM research_projects")
            
            # 커서 닫기
            cursor.close()
            print("Test tables created successfully")
        except Exception as e:
            print(f"Error creating test tables: {str(e)}")
            raise  # 테이블 생성 오류는 테스트를 계속할 수 없으므로 다시 발생시킴
        finally:
            # 연결이 있으면 항상 닫기
            if conn:
                try:
                    conn.close()
                    print("Database connection closed after table creation")
                except Exception as e:
                    print(f"Error closing database connection: {str(e)}")
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        try:
            # 테이블 드롭 로직 주석 처리 (문제 발생 방지)
            # cls._drop_test_tables()
            print("Table drop skipped to avoid issues")
        except Exception as e:
            print(f"Error during tearDown: {str(e)}")
        finally:
            # 임시 디렉토리를 삭제하지 않고 경로 출력
            print(f"==================== 출력 파일 경로 ====================")
            print(f"테스트 파일 디렉토리: {cls.temp_dir}")
            print(f"견적서 PDF 파일: {os.path.join(cls.output_dir, 'test_estimate.pdf')}")
            print(f"출장신청서 PDF 파일: {os.path.join(cls.output_dir, 'test_travel.pdf')}")
            print(f"======================================================")
            
            # 임시 디렉토리 삭제 코드 주석 처리
            # try:
            #     shutil.rmtree(cls.temp_dir)
            #     print(f"Temporary directory {cls.temp_dir} deleted")
            # except Exception as e:
            #     print(f"Error deleting temporary directory: {str(e)}")
            print("Test cleanup completed - Temporary directory preserved for inspection")
    
    @classmethod
    def _drop_test_tables(cls):
        """테스트 테이블 삭제 - 현재 비활성화됨"""
        print("Dropping test tables... (DISABLED)")
        # db_config = cls.config["database"]
        
        # conn = None
        # try:
        #     # DB 연결
        #     conn = psycopg2.connect(
        #         host=db_config["host"],
        #         port=db_config["port"],
        #         user=db_config["user"],
        #         password=db_config["password"],
        #         database=db_config["database"]
        #     )
        #     conn.autocommit = True
        #     cursor = conn.cursor()
            
        #     # 테이블 삭제
        #     cursor.execute("DROP TABLE IF EXISTS companies")
        #     cursor.execute("DROP TABLE IF EXISTS employees")
        #     cursor.execute("DROP TABLE IF EXISTS research_projects")
            
        #     # 커서 닫기
        #     cursor.close()
        #     print("Test tables dropped successfully")
        # except Exception as e:
        #     print(f"Error dropping test tables: {str(e)}")
        # finally:
        #     # 연결이 있으면 항상 닫기
        #     if conn:
        #         try:
        #             conn.close()
        #             print("Database connection closed")
        #         except Exception as e:
        #             print(f"Error closing database connection: {str(e)}")
        
        print("Table drop functionality is disabled to avoid issues")
    
    def setUp(self):
        """테스트 설정"""
        # 문서 서비스 가져오기
        self.document_service = self.container.document_service
        
        # 테스트 데이터 설정
        self.setup_test_data()
    
    def setup_test_data(self):
        """테스트 데이터 설정"""
        # 회사 정보 저장
        company = Company(
            id="COMP-TEST-001",
            company_name="통합테스트 주식회사",
            biz_id="123-45-67890",
            rep_name="김통합",
            address="서울시 강남구",
            biz_type="서비스업",
            biz_item="소프트웨어 개발",
            phone="02-1234-5678",
            rep_stamp=None  # 대표 도장 이미지는 None으로 설정
        )
        self.container.company_repo.save(company)
        
        # 직원 정보 저장
        employee = Employee(
            id="EMP-TEST-001",
            name="이통합",
            department="개발팀",
            position="선임연구원",
            email="test@example.com",
            phone="010-1234-5678",
            bank_name="신한은행",
            account_number="110-123-456789"
        )
        self.container.employee_repo.save(employee)
        
        # 연구 과제 정보 저장
        research = Research(
            id="PROJ-TEST-001",
            project_name="통합테스트 프로젝트",
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="박통합"
        )
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
                },
                {
                    "name": "통합테스트 상품2",
                    "quantity": 1,
                    "unit_price": 30000,
                    "amount": 30000,
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
