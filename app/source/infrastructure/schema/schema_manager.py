import json
import os
import re
from typing import Dict, Any, List, Optional
from core.exceptions import SchemaError
from core.logging import get_logger

logger = get_logger(__name__)

class SchemaManager:
    """JSON 스키마 관리 및 코드 생성"""
    
    def __init__(self, schema_path: str, output_dir: str):
        """초기화"""
        self.schema_path = schema_path
        self.output_dir = output_dir
        
        # 스키마 로드
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            logger.info("Schema loaded successfully", schema_path=schema_path)
        except Exception as e:
            logger.error("Failed to load schema", schema_path=schema_path, error=str(e))
            raise SchemaError(f"Failed to load schema from {schema_path}: {str(e)}")
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        logger.debug("Output directory ensured", output_dir=output_dir)
    
    def generate_all(self):
        """모든 코드 생성"""
        logger.info("Generating all code from schema")
        
        # 데이터 모델 생성
        self.generate_data_models()
        
        # 검증 코드 생성
        self.generate_validators()
        
        # 템플릿 매핑 생성
        self.generate_template_mapping()
        
        # 도메인 데이터 접근 코드 생성
        self.generate_domain_data_access()
        
        # 문서 서비스 생성
        self.generate_document_service()
        
        logger.info("All code generation completed")
    
    def generate_data_models(self):
        """데이터 모델 코드 생성"""
        logger.info("Generating data models")
        output_file = os.path.join(self.output_dir, "data_models.py")
        
        # 모델 코드 생성
        code = self._generate_model_code()
        
        # 파일에 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info("Data models generated", output_file=output_file)
    
    def _generate_model_code(self) -> str:
        """모델 코드 생성"""
        logger.debug("Generating model code")
        
        # 코드 헤더 생성
        code = [
            "# 자동 생성된 코드입니다. 직접 수정하지 마세요.",
            f"# 소스: {os.path.basename(self.schema_path)}",
            "",
            "from pydantic import BaseModel, Field",
            "from typing import List, Dict, Any, Optional, Union",
            "from datetime import date",
            "",
            ""
        ]
        
        # 스키마 정의 가져오기
        definitions = self.schema.get("definitions", self.schema.get("$defs", {}))
        
        # 문서 유형 목록
        document_types = [
            "EstimateDoc", "TradingStatementDoc", "TravelApplicationDoc", 
            "TravelExpenseDoc", "MeetingExpenseDoc", "MeetingMinutesDoc",
            "PurchaseOrderDoc", "ExpertUtilPlanDoc", "ExpertConsultConfirmDoc",
            "ExpenditureDoc"
        ]
        
        # 공통 섹션 모델 생성 (문서가 아닌 클래스)
        for class_name, class_schema in definitions.items():
            if class_name not in document_types:
                logger.debug(f"Generating common section model: {class_name}")
                code.extend(self._generate_model_class(class_name, class_schema))
        
        # 문서 유형별 모델 생성
        for class_name in document_types:
            class_schema = definitions.get(class_name)
            if class_schema:
                logger.debug(f"Generating document model: {class_name}")
                code.extend(self._generate_model_class(class_name, class_schema))
        
        # 최상위 문서 모델 생성
        code.extend([
            "class Document(BaseModel):",
            "    \"\"\"통합 문서 모델\"\"\"",
            "    document_type: str = Field(..., description=\"문서 유형\")"
        ])
        
        # 문서 유형별 조건부 필드 추가
        document_type_mapping = [
            ("견적서", "EstimateDoc"),
            ("거래명세서", "TradingStatementDoc"),
            ("출장신청서", "TravelApplicationDoc"),
            ("출장정산신청서", "TravelExpenseDoc"),
            ("회의비사용신청서", "MeetingExpenseDoc"),
            ("회의록", "MeetingMinutesDoc"),
            ("구매의뢰서", "PurchaseOrderDoc"),
            ("전문가활용계획서", "ExpertUtilPlanDoc"),
            ("전문가자문확인서", "ExpertConsultConfirmDoc"),
            ("지출결의서", "ExpenditureDoc")
        ]
        
        for doc_type, model_name in document_type_mapping:
            field_name = self._camel_to_snake(model_name).replace("_doc", "")
            code.append(f"    {field_name}: Optional[{model_name}] = None")
        
        logger.debug("Model code generation completed")
        return "\n".join(code)
    
    def _generate_model_class(self, class_name: str, class_schema: Dict[str, Any]) -> List[str]:
        """단일 모델 클래스 코드 생성"""
        logger.debug(f"Generating model class: {class_name}")
        
        description = class_schema.get("description", f"{class_name} 모델")
        code = [
            f"class {class_name}(BaseModel):",
            f"    \"\"\"{description}\"\"\"",
        ]
        
        properties = class_schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            field_type = self._get_field_type(prop_schema)
            description = prop_schema.get("description", "")
            
            if description:
                code.append(f"    {prop_name}: {field_type} = Field(None, description=\"{description}\")")
            else:
                code.append(f"    {prop_name}: {field_type} = None")
        
        code.append("")
        return code
    
    def _get_field_type(self, prop_schema: Dict[str, Any]) -> str:
        """스키마 속성에 맞는 필드 타입 결정"""
        # 참조 타입 처리
        if "$ref" in prop_schema:
            ref_path = prop_schema["$ref"]
            ref_class_name = ref_path.split("/")[-1]
            return f"Optional[{ref_class_name}]"
        
        # 배열 타입 처리
        elif prop_schema.get("type") == "array":
            items_schema = prop_schema.get("items", {})
            if "$ref" in items_schema:
                ref_class_name = items_schema["$ref"].split("/")[-1]
                return f"List[{ref_class_name}]"
            else:
                item_type = self._get_json_type_to_python(items_schema.get("type", "string"))
                return f"List[{item_type}]"
        
        # 기본 타입 처리
        else:
            return f"Optional[{self._get_json_type_to_python(prop_schema.get('type', 'string'))}]"
    
    def _get_json_type_to_python(self, json_type: str) -> str:
        """JSON 스키마 타입을 Python 타입으로 변환"""
        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "object": "Dict[str, Any]",
            "null": "None",
            "array": "List[Any]"
        }
        return type_mapping.get(json_type, "Any")
    
    def _camel_to_snake(self, name: str) -> str:
        """카멜 케이스를 스네이크 케이스로 변환"""
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    def generate_validators(self):
        """검증 코드 생성"""
        logger.info("Generating validators")
        output_file = os.path.join(self.output_dir, "validators.py")
        
        # 검증 코드 생성
        code = [
            "# 자동 생성된 코드입니다. 직접 수정하지 마세요.",
            f"# 소스: {os.path.basename(self.schema_path)}",
            "",
            "import json",
            "import jsonschema",
            "from jsonschema import validate",
            "from typing import Dict, Any, Optional, Tuple",
            "from core.interfaces import SchemaValidator",
            "from core.exceptions import ValidationError, SchemaError",
            "from core.logging import get_logger",
            "",
            "logger = get_logger(__name__)",
            "",
            "class JsonSchemaValidator(SchemaValidator):",
            "    \"\"\"JSON 스키마를 사용한 데이터 검증\"\"\"",
            "    ",
            "    def __init__(self, schema_path: str):",
            "        logger.debug(\"Initializing JsonSchemaValidator\", schema_path=schema_path)",
            "        try:",
            "            with open(schema_path, 'r', encoding='utf-8') as f:",
            "                self.schema = json.load(f)",
            "            logger.info(\"Schema loaded successfully\", schema_path=schema_path)",
            "        except Exception as e:",
            "            logger.error(\"Failed to load schema\", schema_path=schema_path, error=str(e))",
            "            raise SchemaError(f\"Failed to load schema from {schema_path}: {str(e)}\")",
            "    ",
            "    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:",
            "        \"\"\"데이터가 스키마에 맞는지 검증\"\"\"",
            "        logger.debug(\"Validating data against schema\", document_type=data.get(\"document_type\", \"unknown\"))",
            "        try:",
            "            validate(instance=data, schema=self.schema)",
            "            logger.debug(\"Data validation successful\")",
            "            return True, None",
            "        except jsonschema.exceptions.ValidationError as e:",
            "            logger.warning(\"Data validation failed\", error=str(e))",
            "            return False, str(e)",
            "    ",
            "    def validate_document_type(self, document_type: str) -> bool:",
            "        \"\"\"문서 유형이 유효한지 검증\"\"\"",
            "        logger.debug(\"Validating document type\", document_type=document_type)",
            "        valid_types = self.schema.get(\"properties\", {}).get(\"document_type\", {}).get(\"enum\", [])",
            "        is_valid = document_type in valid_types",
            "        ",
            "        if is_valid:",
            "            logger.debug(\"Document type is valid\", document_type=document_type)",
            "        else:",
            "            logger.warning(\"Invalid document type\", document_type=document_type, valid_types=valid_types)",
            "        ",
            "        return is_valid"
        ]
        
        # 파일에 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(code))
        
        logger.info("Validators generated", output_file=output_file)
    
    def generate_template_mapping(self):
        """템플릿 매핑 코드 생성"""
        logger.info("Generating template mapping")
        output_file = os.path.join(self.output_dir, "template_mapping.py")
        
        # 템플릿 매핑 코드 생성
        code = [
            "# 자동 생성된 코드입니다. 직접 수정하지 마세요.",
            f"# 소스: {os.path.basename(self.schema_path)}",
            "",
            "from typing import Dict, Any",
            "from core.logging import get_logger",
            "",
            "logger = get_logger(__name__)",
            "",
            "def get_template_name(document_type: str) -> str:",
            "    \"\"\"문서 유형에 맞는 템플릿 파일명 반환\"\"\"",
            "    mapping = {",
            "        \"견적서\": \"documents/estimate.html\",",
            "        \"거래명세서\": \"documents/trading_statement.html\",",
            "        \"출장신청서\": \"documents/travel_application.html\",",
            "        \"출장정산신청서\": \"documents/travel_expense.html\",",
            "        \"회의비사용신청서\": \"documents/meeting_expense.html\",",
            "        \"회의록\": \"documents/meeting_minutes.html\",",
            "        \"구매의뢰서\": \"documents/purchase_order.html\",",
            "        \"전문가활용계획서\": \"documents/expert_util_plan.html\",",
            "        \"전문가자문확인서\": \"documents/expert_consult_confirm.html\",",
            "        \"지출결의서\": \"documents/expenditure.html\"",
            "    }",
            "    ",
            "    if document_type not in mapping:",
            "        logger.error(\"Unsupported document type\", document_type=document_type)",
            "        raise ValueError(f\"Unsupported document type: {document_type}\")",
            "    ",
            "    logger.debug(\"Template name resolved\", document_type=document_type, template=mapping[document_type])",
            "    return mapping[document_type]"
        ]
        
        # 파일에 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(code))
        
        logger.info("Template mapping generated", output_file=output_file)
    
    def generate_domain_data_access(self):
        """도메인 데이터 접근 코드 생성"""
        logger.info("Generating domain data access")
        output_file = os.path.join(self.output_dir, "domain_data.py")
        
        # 도메인 데이터 접근 코드 생성
        code = [
            "# 자동 생성된 코드입니다. 직접 수정하지 마세요.",
            f"# 소스: {os.path.basename(self.schema_path)}",
            "",
            "from typing import Dict, Any, List, Optional",
            "from core.interfaces import Repository",
            "from core.domain import Company, Employee, Research, Expert",
            "from core.logging import get_logger",
            "",
            "logger = get_logger(__name__)",
            "",
            "class DomainDataService:",
            "    \"\"\"도메인 데이터 접근 서비스\"\"\"",
            "    ",
            "    def __init__(self,",
            "                 company_repo: Repository[Company],",
            "                 employee_repo: Repository[Employee],",
            "                 research_repo: Repository[Research],",
            "                 expert_repo: Repository[Expert]):",
            "        self.company_repo = company_repo",
            "        self.employee_repo = employee_repo",
            "        self.research_repo = research_repo",
            "        self.expert_repo = expert_repo",
            "        logger.debug(\"DomainDataService initialized\")",
            "    ",
            "    def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:",
            "        \"\"\"회사 정보 조회\"\"\"",
            "        logger.debug(\"Getting company data\", company_id=company_id)",
            "        company = self.company_repo.find_by_id(company_id)",
            "        ",
            "        if not company:",
            "            logger.warning(\"Company not found\", company_id=company_id)",
            "            return None",
            "        ",
            "        # 딕셔너리로 변환",
            "        company_dict = {k: v for k, v in company.__dict__.items()}",
            "        logger.debug(\"Company data retrieved\", company_id=company_id)",
            "        return company_dict",
            "    ",
            "    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:",
            "        \"\"\"직원 정보 조회\"\"\"",
            "        logger.debug(\"Getting employee data\", employee_id=employee_id)",
            "        employee = self.employee_repo.find_by_id(employee_id)",
            "        ",
            "        if not employee:",
            "            logger.warning(\"Employee not found\", employee_id=employee_id)",
            "            return None",
            "        ",
            "        # 딕셔너리로 변환",
            "        employee_dict = {k: v for k, v in employee.__dict__.items()}",
            "        logger.debug(\"Employee data retrieved\", employee_id=employee_id)",
            "        return employee_dict",
            "    ",
            "    def get_research(self, research_id: str) -> Optional[Dict[str, Any]]:",
            "        \"\"\"연구 과제 정보 조회\"\"\"",
            "        logger.debug(\"Getting research data\", research_id=research_id)",
            "        research = self.research_repo.find_by_id(research_id)",
            "        ",
            "        if not research:",
            "            logger.warning(\"Research not found\", research_id=research_id)",
            "            return None",
            "        ",
            "        # 딕셔너리로 변환",
            "        research_dict = {k: v for k, v in research.__dict__.items()}",
            "        logger.debug(\"Research data retrieved\", research_id=research_id)",
            "        return research_dict",
            "    ",
            "    def get_expert(self, expert_id: str) -> Optional[Dict[str, Any]]:",
            "        \"\"\"전문가 정보 조회\"\"\"",
            "        logger.debug(\"Getting expert data\", expert_id=expert_id)",
            "        expert = self.expert_repo.find_by_id(expert_id)",
            "        ",
            "        if not expert:",
            "            logger.warning(\"Expert not found\", expert_id=expert_id)",
            "            return None",
            "        ",
            "        # 딕셔너리로 변환",
            "        expert_dict = {k: v for k, v in expert.__dict__.items()}",
            "        logger.debug(\"Expert data retrieved\", expert_id=expert_id)",
            "        return expert_dict"
        ]
        
        # 파일에 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(code))
        
        logger.info("Domain data access generated", output_file=output_file)
    
    def generate_document_service(self):
        """문서 서비스 코드 생성"""
        logger.info("Generating document service")
        output_file = os.path.join(self.output_dir, "document_service.py")
        
        # 문서 서비스 코드 생성
        code = [
            "# 자동 생성된 코드입니다. 직접 수정하지 마세요.",
            f"# 소스: {os.path.basename(self.schema_path)}",
            "",
            "from typing import Dict, Any, Optional",
            "import os",
            "import uuid",
            "from datetime import datetime",
            "from core.interfaces import SchemaValidator, DataEnricher, DocumentRenderer, PdfGenerator",
            "from core.exceptions import ValidationError, RenderingError, PdfGenerationError",
            "from core.logging import get_logger",
            "",
            "logger = get_logger(__name__)",
            "",
            "class DocumentService:",
            "    \"\"\"문서 생성 및 관리 서비스\"\"\"",
            "    ",
            "    def __init__(",
            "        self,",
            "        validator: SchemaValidator,",
            "        data_enricher: DataEnricher,",
            "        renderer: DocumentRenderer,",
            "        pdf_generator: PdfGenerator",
            "    ):",
            "        self.validator = validator",
            "        self.data_enricher = data_enricher",
            "        self.renderer = renderer",
            "        self.pdf_generator = pdf_generator",
            "        logger.debug(\"DocumentService initialized\")",
            "    ",
            "    def create_document(self, data: Dict[str, Any]) -> Dict[str, Any]:",
            "        \"\"\"문서 생성\"\"\"",
            "        document_type = data.get(\"document_type\")",
            "        logger.info(\"Creating document\", document_type=document_type)",
            "        ",
            "        # 데이터 검증",
            "        is_valid, error = self.validator.validate(data)",
            "        if not is_valid:",
            "            logger.error(\"Document data validation failed\", error=error)",
            "            raise ValidationError(f\"Invalid document data: {error}\")",
            "        ",
            "        # 데이터 보강",
            "        enriched_data = self.data_enricher.enrich(document_type, data)",
            "        logger.debug(\"Document data enriched\")",
            "        ",
            "        # HTML 렌더링",
            "        try:",
            "            html = self.renderer.render(document_type, enriched_data)",
            "            logger.debug(\"Document rendered to HTML\", html_length=len(html))",
            "        except RenderingError as e:",
            "            logger.error(\"Document rendering failed\", error=str(e))",
            "            raise",
            "        ",
            "        # PDF 생성",
            "        try:",
            "            pdf = self.pdf_generator.generate(html)",
            "            logger.debug(\"PDF generated\", pdf_size=len(pdf))",
            "        except PdfGenerationError as e:",
            "            logger.error(\"PDF generation failed\", error=str(e))",
            "            raise",
            "        ",
            "        # 결과 반환",
            "        result = {",
            "            \"document_id\": str(uuid.uuid4()),",
            "            \"document_type\": document_type,",
            "            \"created_at\": datetime.now().isoformat(),",
            "            \"html\": html,",
            "            \"pdf\": pdf",
            "        }",
            "        ",
            "        logger.info(\"Document created successfully\", ",
            "                   document_id=result[\"document_id\"],",
            "                   document_type=result[\"document_type\"],",
            "                   created_at=result[\"created_at\"],",
            "                   html_length=len(result[\"html\"]),",
            "                   pdf_size=len(result[\"pdf\"]))",
            "        ",
            "        return result",
            "    ",
            "    def save_pdf(self, pdf_data: bytes, output_path: str) -> str:",
            "        \"\"\"PDF 파일 저장\"\"\"",
            "        logger.debug(\"Saving PDF to file\", output_path=output_path)",
            "        ",
            "        # 디렉토리 확인 및 생성",
            "        output_dir = os.path.dirname(output_path)",
            "        if output_dir and not os.path.exists(output_dir):",
            "            os.makedirs(output_dir)",
            "            logger.debug(\"Created output directory\", directory=output_dir)",
            "        ",
            "        # PDF 저장",
            "        try:",
            "            with open(output_path, 'wb') as f:",
            "                f.write(pdf_data)",
            "            ",
            "            logger.info(\"PDF saved successfully\", output_path=output_path, size=len(pdf_data))",
            "            return output_path",
            "        except Exception as e:",
            "            logger.error(\"Failed to save PDF\", output_path=output_path, error=str(e))",
            "            raise IOError(f\"Failed to save PDF to {output_path}: {str(e)}\")"
        ]
        
        # 파일에 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(code))
        
        logger.info("Document service generated", output_file=output_file)
