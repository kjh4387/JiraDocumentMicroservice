from app.source.application.services.document_service import DocumentService
from app.source.application.services.document_processor import ConfigurableDocumentProcessor
from app.source.application.services.field_processors import (
    StringFieldProcessor, NumberFieldProcessor, DateFieldProcessor,
    DateRangeFieldProcessor, ArrayFieldProcessor
)
from app.source.application.services.preprocessors import MarkdownTablePreprocessor
from app.source.application.services.post_processors import (
    DocumentNumberGenerator, ItemAmountCalculator, TotalAmountCalculator, TaxCalculator
)
from app.source.core.schema_registry import SchemaRegistry
from app.source.infrastructure.repositories import (
    EmployeeRepository, CompanyRepository, ProjectRepository, ExpertRepository
)
from app.source.infrastructure.counter_service import CounterService

def create_document_service(db_client):
    """문서 처리 서비스 생성"""
    
    # 1. 레포지토리 초기화
    repositories = {
        "employee": EmployeeRepository(db_client),
        "company": CompanyRepository(db_client),
        "research_project": ProjectRepository(db_client),
        "expert": ExpertRepository(db_client)
    }
    
    # 2. 스키마 레지스트리 초기화
    schema_registry = SchemaRegistry()
    
    # 출장신청서 설정 등록
    schema_registry.register_document_config("출장신청서", {
        "direct_fields": {
            "travel_purpose": {"type": "string", "required": True, "max_length": 100},
            "travel_period": {"type": "date_range", "required": True},
            "destination": {"type": "string", "required": True},
            "transportation": {"type": "string", "required": True, "choices": ["KTX", "버스", "비행기", "자가용", "기타"]},
            "accommodation": {"type": "string", "required": False},
            "estimated_expense": {"type": "number", "required": True, "min_value": 0},
            "special_note": {"type": "string", "required": False}
        },
        "reference_fields": [
            {
                "field": "applicant_email",
                "entity_type": "employee",
                "lookup_field": "email",
                "target_path": "applicant",
                "fields": ["name", "employee_id", "department", "position", "contact", "signature_image_url"]
            },
            {
                "field": "travel_list",
                "entity_type": "employee",
                "lookup_field": "email",
                "target_path": "travelers",
                "fields": ["name", "employee_id", "department", "position", "contact"],
                "is_array": True
            },
            {
                "field": "research_project_id",
                "entity_type": "research_project",
                "lookup_field": "id",
                "target_path": "research_project_info",
                "fields": ["name", "code", "period", "manager"]
            },
            {
                "field": "approver_emails",
                "entity_type": "employee",
                "lookup_field": "email",
                "target_path": "approval_list",
                "fields": ["name", "employee_id", "department", "position", "signature_image_url"],
                "is_array": True,
                "additional_processing": "add_approval_order"
            }
        ],
        "post_processors": ["DocumentNumberGenerator", "TravelDurationCalculator"]
    })
    
    # 견적서 설정 등록
    schema_registry.register_document_config("견적서", {
        "direct_fields": {
            "issue_date": {"type": "date", "required": True},
            "valid_until": {"type": "date", "required": True},
            "payment_terms": {"type": "string", "required": False},
            "items_table": {"type": "string", "required": True}  # 마크다운 테이블
        },
        "reference_fields": [
            {
                "field": "supplier_company_id",
                "entity_type": "company",
                "lookup_field": "id",
                "target_path": "supplier",
                "fields": ["name", "address", "representative", "business_number", "tel", "fax", "email"]
            },
            {
                "field": "customer_company_id",
                "entity_type": "company",
                "lookup_field": "id",
                "target_path": "customer",
                "fields": ["name", "address", "representative", "business_number", "tel", "fax", "email"]
            },
            {
                "field": "issuer_email",
                "entity_type": "employee",
                "lookup_field": "email",
                "target_path": "issuer",
                "fields": ["name", "department", "position", "contact", "signature_image_url"]
            },
            {
                "field": "project_code",
                "entity_type": "research_project",
                "lookup_field": "code",
                "target_path": "project",
                "fields": ["name", "manager", "description"]
            }
        ],
        "post_processors": ["DocumentNumberGenerator", "ItemAmountCalculator", "TotalAmountCalculator", "TaxCalculator"]
    })
    
    # 전문가활용계획서 설정 등록
    schema_registry.register_document_config("전문가활용계획서", {
        "direct_fields": {
            "issue_date": {"type": "date", "required": True},
            "purpose": {"type": "string", "required": True, "max_length": 200},
            "utilization_period": {"type": "date_range", "required": True},
            "total_hours": {"type": "number", "required": True, "min_value": 1},
            "hourly_rate": {"type": "number", "required": True, "min_value": 0},
            "total_amount": {"type": "number", "required": False}
        },
        "reference_fields": [
            {
                "field": "expert_id",
                "entity_type": "expert",
                "lookup_field": "id",
                "target_path": "expert_info",
                "fields": ["name", "affiliation", "position", "specialty", "contact", "email", "bank_account"]
            },
            {
                "field": "requester_email",
                "entity_type": "employee",
                "lookup_field": "email",
                "target_path": "requester",
                "fields": ["name", "employee_id", "department", "position", "signature_image_url"]
            },
            {
                "field": "approver_emails",
                "entity_type": "employee",
                "lookup_field": "email",
                "target_path": "approval_list",
                "fields": ["name", "employee_id", "department", "position", "signature_image_url"],
                "is_array": True,
                "additional_processing": "add_approval_order"
            }
        ],
        "post_processors": ["DocumentNumberGenerator", "TotalAmountCalculator", "PeriodDurationCalculator"]
    })
    
    # 다른 문서 유형 설정 등록...
    
    # 3. 필드 처리기 초기화
    field_processors = {
        "string": StringFieldProcessor(),
        "number": NumberFieldProcessor(),
        "date": DateFieldProcessor(),
        "date_range": DateRangeFieldProcessor(),
        "array": ArrayFieldProcessor()
    }
    
    # 4. 카운터 서비스 초기화
    counter_service = CounterService(db_client)
    
    # 5. 후처리기 초기화
    document_number_generator = DocumentNumberGenerator(counter_service)
    item_amount_calculator = ItemAmountCalculator()
    total_amount_calculator = TotalAmountCalculator()
    
    # 6. 문서 처리기 초기화
    document_processor = ConfigurableDocumentProcessor(
        schema_registry,
        field_processors,
        repositories
    )
    
    # 후처리기 등록
    document_processor.register_post_processor(
        "DocumentNumberGenerator", document_number_generator
    )
    document_processor.register_post_processor(
        "ItemAmountCalculator", item_amount_calculator
    )
    document_processor.register_post_processor(
        "TotalAmountCalculator", total_amount_calculator
    )
    
    # 7. 전처리기 초기화
    field_mapping = {
        "items_table": {
            "target": "items",
            "columns": ["name", "quantity", "unit_price", "specification"],
            "remove_source": True
        }
    }
    preprocessors = [
        MarkdownTablePreprocessor(field_mapping)
    ]
    
    # 8. 문서 서비스 생성
    document_service = DocumentService(
        preprocessors=preprocessors,
        document_processor=document_processor,
        repositories=repositories
    )
    
    return document_service 