import unittest
import os
import tempfile
import shutil
import psycopg2
from app.source.config.di_container import DIContainer
from app.source.core.exceptions import DocumentAutomationError
# 명시적으로 각 도메인 클래스 임포트
from app.source.core.domain import Company, Employee, Research, Expert
from datetime import date

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
        
        # 테스트 테이블 삭제 및 재생성
        cls._drop_test_tables_if_exist()
        cls._create_test_tables()
        
        # 의존성 주입 컨테이너 초기화
        cls.container = DIContainer(cls.config)
    
    @classmethod
    def _drop_test_tables_if_exist(cls):
        """기존 테스트 테이블이 있으면 삭제"""
        print("Dropping existing test tables if they exist...")
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
            
            tables = ["companies", "employees", "research_projects", "experts"]
            #for table in tables:
            #    cursor.execute(f"DROP TABLE IF EXISTS {table}")
            #    print(f"Dropped table {table} if it existed")
            
            # 커서 닫기
            cursor.close()
            print("Existing tables dropped successfully")
        except Exception as e:
            print(f"Error dropping test tables: {str(e)}")
        finally:
            # 연결이 있으면 항상 닫기
            if conn:
                conn.close()
    
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
            
            # 회사 테이블 생성 - 모든 필수 필드 포함
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    biz_id TEXT NOT NULL,
                    rep_name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    biz_type TEXT NOT NULL,
                    biz_item TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    rep_stamp BYTEA,
                    email TEXT,
                    fax TEXT
                )
            """)
            
            # 직원 테이블 생성 - 모든 필수 필드 포함
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    position TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    signature TEXT,
                    stamp TEXT,
                    bank_name TEXT,
                    account_number TEXT,
                    birth_date TEXT,
                    address TEXT,
                    fax TEXT
                )
            """)
            
            # 연구 과제 테이블 생성 - 모든 필수 필드 포함
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_projects (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    project_code TEXT NOT NULL,
                    project_period TEXT,
                    project_manager TEXT,
                    project_start_date DATE,
                    project_end_date DATE,
                    budget NUMERIC,
                    status TEXT,
                    description TEXT
                )
            """)
            
            # 전문가 테이블 생성 - 추가
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    affiliation TEXT,
                    position TEXT,
                    birth_date DATE,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    bank_name TEXT,
                    account_number TEXT,
                    specialty TEXT,
                    bio TEXT
                )
            """)
            
            # 기존 데이터 정리
            cursor.execute("DELETE FROM companies")
            cursor.execute("DELETE FROM employees")
            cursor.execute("DELETE FROM research_projects")
            cursor.execute("DELETE FROM experts")
            
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
    def clean_test_data(cls):
        """테스트 데이터 정리"""
        print("테스트 데이터 정리 중...")
        
        # DB 연결 설정
        db_config = cls.config["database"]
        
        import psycopg2
        conn = None
        
        try:
            conn = psycopg2.connect(**db_config)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # 테스트 데이터 삭제
            tables = [
                "companies", 
                "employees", 
                "research_projects", 
                "experts",
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"DELETE FROM {table} WHERE id LIKE '%TEST%'")
                    print(f"{table} 테이블 테스트 데이터 삭제 완료")
                except Exception as e:
                    print(f"{table} 테이블 정리 중 오류: {str(e)}")
            
            print("테스트 데이터 정리 완료")
            
        except Exception as e:
            print(f"데이터 정리 중 오류 발생: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
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
            rep_stamp=None,  # 대표 도장 이미지는 None으로 설정
            fax="02-1234-5679",
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
            account_number="110-123-456789",
            signature=None,
            stamp=None,  # None으로 설정
            birth_date="1990-01-01",
            address="서울시 서초구",
            fax="02-1234-5679"
        )
        self.container.employee_repo.save(employee)
        
        # 연구 과제 정보 저장
        research = Research(
            id="RESEARCH-TEST-001",
            project_name="통합테스트 연구과제",
            project_code="R2023-001",
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="김관리",
            project_start_date=date(2023, 1, 1),
            project_end_date=date(2023, 12, 31),
            budget=100000000,
            status="진행중",
            description="테스트 연구과제 설명"
        )
        self.container.research_repo.save(research)
        
        # 전문가 정보 저장
        expert = Expert(
            id="EXP-TEST-001",
            name="김전문",
            affiliation="서울대학교",
            position="교수",
            email="expert@example.com",
            birth_date=date(1970, 5, 15),
            phone="010-1234-5678",
            address="서울시 관악구",
            bank_name="국민은행",
            account_number="110-987-654321",
            specialty="인공지능",
            bio="인공지능 분야 전문가"
        )
        self.container.expert_repo.save(expert)
    
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
                "company_name": "통합테스트 주식회사"
            },
            "item_list": [
                {
                    "name": "통합테스트 상품",
                    "quantity": 2,
                    "unit_price": 50000,
                    "amount": 100000,
                    "spec": "A급"
                },
                {
                    "name": "통합테스트 상품2",
                    "quantity": 1,
                    "unit_price": 30000,
                    "amount": 30000,
                    "spec": "B급"
                }
            ],
            "amount_summary": {
                "supply_sum": 130000,
                "vat_sum": 13000,
                "grand_total": 143000
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
                "project_code": "R2023-001"
            },
            "travel_list": [
                {
                    "email": "test@example.com",
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

    def test_trading_statement_document_flow(self):
        """거래명세서 생성 흐름 테스트"""
        # 테스트 데이터
        trading_data = {
            "document_type": "거래명세서",
            "metadata": {
                "document_number": "TR-TEST-001",
                "date_issued": "2023-05-20",
                "receiver": "수신자"
            },
            "supplier_info": {
                "company_name": "통합테스트 주식회사"
            },
            "customer_info": {
                "company_name": "통합테스트 주식회사"
            },
            "item_list": [
                {
                    "name": "거래 상품1",
                    "spec": "규격A",
                    "quantity": 3,
                    "unit_price": 40000,
                    "amount": 120000,
                    "vat": 12000
                },
                {
                    "name": "거래 상품2",
                    "spec": "규격B",
                    "quantity": 2,
                    "unit_price": 25000,
                    "amount": 50000,
                    "vat": 5000
                }
            ],
            "amount_summary": {
                "supply_sum": 170000,
                "vat_sum": 17000,
                "grand_total": 187000
            }
        }
        
        # 문서 생성
        result = self.document_service.create_document(trading_data)
        
        # 검증
        self.assertEqual(result["document_type"], "거래명세서")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_trading_statement.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)

    def test_travel_expense_document_flow(self):
        """출장정산신청서 생성 흐름 테스트"""
        # 테스트 데이터
        expense_data = {
            "document_type": "출장정산신청서",
            "metadata": {
                "document_number": "EXP-TEST-001",
                "date_issued": "2023-06-25",
                "reference_document_id": "TRAVEL-TEST-001"
            },
            "research_project_info": {
                "project_code": "R2023-001"
            },
            "traveler_info": {
                "email": "test@example.com"
            },
            "expense_list": [
                {
                    "date": "2023-06-01",
                    "category": "교통비",
                    "detail": "KTX 왕복",
                    "amount": 120000,
                    "receipt": "receipt1.jpg"
                },
                {
                    "date": "2023-06-01~03",
                    "category": "숙박비",
                    "detail": "호텔 2박",
                    "amount": 200000,
                    "receipt": "receipt2.jpg"
                }
            ],
            "amount_summary": {
                "advance_payment": 300000,
                "total_expense": 320000,
                "balance": -20000
            }
        }
        
        # 문서 생성
        result = self.document_service.create_document(expense_data)
        
        # 검증
        self.assertEqual(result["document_type"], "출장정산신청서")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_travel_expense.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)
    
    def test_meeting_expense_document_flow(self):
        """회의비사용신청서 생성 흐름 테스트"""
        # 테스트 데이터
        meeting_expense_data = {
            "document_type": "회의비사용신청서",
            "metadata": {
                "document_number": "ME-TEST-001",
                "date_issued": "2023-07-05"
            },
            "research_project_info": {
                "project_code": "R2023-001"
            },
            "meeting_info": {
                "date": "2023-07-04 14:00~16:00",
                "place": "회의실 A",
                "purpose": "프로젝트 진행상황 검토",
                "participants": "이통합, 김개발, 박디자인"
            },
            "expense_info": {
                "expense_type": "식비",
                "amount": 120000,
                "payment_method": "법인카드"
            },
            "applicant_info": {
                "apply_date": "2023-07-05",
                "email": "test@example.com"
            }
        }
        
        # 문서 생성
        result = self.document_service.create_document(meeting_expense_data)
        
        # 검증
        self.assertEqual(result["document_type"], "회의비사용신청서")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_meeting_expense.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)
    
    def test_meeting_minutes_document_flow(self):
        """회의록 생성 흐름 테스트"""
        # 테스트 데이터
        minutes_data = {
            "document_type": "회의록",
            "metadata": {
                "document_number": "MM-TEST-001",
                "date_issued": "2023-07-05"
            },
            "research_project_info": {
                "project_code": "R2023-001"
            },
            "meeting_info": {
                "title": "7월 정기 회의",
                "date": "2023-07-04 14:00~16:00",
                "place": "회의실 A",
                "participants": "이통합(PM), 김개발(개발), 박디자인(디자인)"
            },
            "meeting_content": {
                "agenda": "1. 전월 진행상황 점검\n2. 이슈 사항 논의\n3. 향후 일정 계획",
                "discussion": "- 전월 계획된 모듈 개발이 완료됨\n- 테스트 과정에서 성능 이슈 발견\n- 고객사 요구사항 일부 변경 필요",
                "conclusion": "성능 이슈 해결 후 고객사와 요구사항 변경 협의 진행하기로 결정",
                "action_items": "1. 김개발: 성능 최적화 진행 (7/15까지)\n2. 이통합: 고객사 미팅 일정 조율 (7/10까지)"
            },
            "writer_info": {
                "email": "test@example.com",
                "name": "이통합",
                "position": "PM",
                "department": "개발팀"
            }
        }
        
        # 문서 생성
        result = self.document_service.create_document(minutes_data)
        
        # 검증
        self.assertEqual(result["document_type"], "회의록")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_meeting_minutes.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)
    
    def test_purchase_order_document_flow(self):
        """구매의뢰서 생성 흐름 테스트"""
        # 테스트 데이터
        purchase_data = {
            "document_type": "구매의뢰서",
            "metadata": {
                "document_number": "PO-TEST-001",
                "date_issued": "2023-07-10"
            },
            "research_project_info": {
                "project_code": "R2023-001"
            },
            "purchase_reason": "프로젝트 개발 환경 구축",
            "item_list": [
                {
                    "name": "개발용 노트북",
                    "spec": "i7, 16GB RAM, 512GB SSD",
                    "quantity": 2,
                    "unit_price": 1500000,
                    "amount": 3000000,
                    "purpose": "개발자 작업용"
                },
                {
                    "name": "모니터",
                    "spec": "27인치 4K",
                    "quantity": 2,
                    "unit_price": 500000,
                    "amount": 1000000,
                    "purpose": "개발 환경용"
                }
            ],
            "amount_summary": {
                "supply_sum": 4000000,
                "vat_sum": 400000,
                "grand_total": 4400000
            },
            "applicant_info": {
                "apply_date": "2023-07-10",
                "email": "test@example.com"
            }
        }
        
        # 문서 생성
        result = self.document_service.create_document(purchase_data)
        
        # 검증
        self.assertEqual(result["document_type"], "구매의뢰서")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_purchase_order.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)
    
    def test_expert_plan_document_flow(self):
        """전문가활용계획서 생성 흐름 테스트"""
        # 테스트 데이터
        expert_plan_data = {
            "document_type": "전문가활용계획서",
            "metadata": {
                "document_number": "EP-TEST-001",
                "date_issued": "2023-07-15"
            },
            "research_project_info": {
                "project_code": "R2023-001"
            },
            "expert_info": {
                "name": "김전문",
                "affiliation": "서울대학교",
                "position": "교수",
                "birth_date": "1970-05-15",
                "email": "expert@example.com",
                "phone": "010-1234-5678",
                "address": "서울시 관악구"
            },
            "util_plan": {
                "start_date": "2023-08-01",
                "end_date": "2023-08-31",
                "purpose": "딥러닝 모델 설계 자문",
                "content": "프로젝트 데이터 분석 및 모델 아키텍처 검토",
                "fee": 1500000
            },
            "applicant_info": {
                "apply_date": "2023-07-15",
                "email": "test@example.com"
            }
        }
        
        # 문서 생성
        result = self.document_service.create_document(expert_plan_data)
        
        # 검증
        self.assertEqual(result["document_type"], "전문가활용계획서")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_expert_plan.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)
    
    def test_expert_confirm_document_flow(self):
        """전문가자문확인서 생성 흐름 테스트"""
        # 테스트 데이터
        expert_confirm_data = {
            "document_type": "전문가자문확인서",
            "metadata": {
                "document_number": "EC-TEST-001",
                "date_issued": "2023-08-31"
            },
            "research_project_info": {
                "project_code": "R2023-001"
            },
            "expert_info": {
                "expert_id": "EXP-001",
                "name": "김전문",
                "affiliation": "서울대학교",
                "position": "교수",
                "dob": "1970-05-15",
                "email": "expert@example.com",
                "phone": "010-1234-5678",
                "address": "서울시 관악구"
            },
            "consult_result": {
                "date": "2023-08-15",
                "place": "서울대학교 연구실",
                "method": "대면 회의",
                "content": "1. 데이터 전처리 방법 검토\n2. 모델 아키텍처 최적화 방안 제시\n3. 성능 평가 지표 선정",
                "fee": 1500000
            },
            "applicant_info": {
                "apply_date": "2023-08-31",
                "email": "test@example.com"
            }
        }
        
        # 문서 생성
        result = self.document_service.create_document(expert_confirm_data)
        
        # 검증
        self.assertEqual(result["document_type"], "전문가자문확인서")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_expert_confirm.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)
    
    def test_expenditure_document_flow(self):
        """지출결의서 생성 흐름 테스트"""
        # 테스트 데이터
        expenditure_data = {
            "document_type": "지출결의서",
            "metadata": {
                "document_number": "EX-TEST-001",
                "date_issued": "2023-09-05",
                "writer": "이통합",
                "department": "개발팀",
                "purpose": "프로젝트 장비 구매 비용"
            },
            "research_project_info": {
                "project_code": "R2023-001"
            },
            "expense_list": [
                {
                    "item_name": "노트북 구매",
                    "amount": 3000000,
                    "memo": "인보이스 #INV-001"
                },
                {
                    "item_name": "모니터 구매",
                    "amount": 1000000,
                    "memo": "인보이스 #INV-002"
                }
            ],
            "amount_summary": {
                "supply_sum": 4000000,
                "vat_sum": 400000,
                "grand_total": 4400000,
                "total_in_korean": "사백사십만원정"
            },
            "applicant_info": {
                "apply_date": "2023-09-05",
                "email": "test@example.com"
            },
            "approval_list": [
                {
                    "email": "boss@example.com",
                    "name": "김부장",
                    "position": "부장",
                    "department": "개발팀",
                    "approval_status": "승인",
                    "approval_date": "2023-09-06"
                }
            ]
        }
        
        # 문서 생성
        result = self.document_service.create_document(expenditure_data)
        
        # 검증
        self.assertEqual(result["document_type"], "지출결의서")
        self.assertIn("<html", result["html"])
        self.assertIsInstance(result["pdf"], bytes)
        
        # PDF 저장
        output_path = os.path.join(self.output_dir, "test_expenditure.pdf")
        saved_path = self.document_service.save_pdf(result["pdf"], output_path)
        
        # 파일 존재 확인
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(os.path.getsize(saved_path) > 0)

    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        try:
            # 테스트 데이터 정리
            cls.clean_test_data()
            
            # 이제 테이블도 삭제 
            cls._drop_test_tables_if_exist()
            print("Test tables dropped during tearDown")
        except Exception as e:
            print(f"Error during tearDown: {str(e)}")
        finally:
            # 임시 디렉토리를 삭제하지 않고 경로 출력
            print(f"==================== 출력 파일 경로 ====================")
            print(f"테스트 파일 디렉토리: {cls.temp_dir}")
            print(f"견적서 PDF 파일: {os.path.join(cls.output_dir, 'test_estimate.pdf')}")
            print(f"출장신청서 PDF 파일: {os.path.join(cls.output_dir, 'test_travel.pdf')}")
            print(f"======================================================")
            
            # 임시 디렉토리 삭제 코드 주석 처리 - 파일 검사를 위해 유지
            # try:
            #     shutil.rmtree(cls.temp_dir)
            #     print(f"Temporary directory {cls.temp_dir} deleted")
            # except Exception as e:
            #     print(f"Error deleting temporary directory: {str(e)}")
            print("Test cleanup completed - Temporary directory preserved for inspection")

if __name__ == '__main__':
    unittest.main()
