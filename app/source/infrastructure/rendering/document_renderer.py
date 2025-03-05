from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from app.source.core.interfaces import DocumentRenderer
from app.source.core.exceptions import RenderingError
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class JinjaDocumentRenderer(DocumentRenderer):
    """Jinja2를 사용한 문서 렌더링"""
    
    def __init__(self, template_dir: str):
        """템플릿 디렉토리 경로로 초기화"""
        logger.debug("Initializing JinjaDocumentRenderer", template_dir=template_dir)
        try:
            self.template_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=True
            )
            
            # 날짜 포맷팅 필터 추가
            self.template_env.filters['format_date'] = self._format_date
            
            logger.info("Jinja2 environment initialized")
        except Exception as e:
            logger.error("Failed to initialize Jinja2 environment", error=str(e))
            raise RenderingError(f"Failed to initialize document renderer: {str(e)}")
    
    def _format_date(self, value, format_string=None):
        """날짜 포맷팅 필터"""
        if not value:
            return ""
        
        try:
            # 문자열이면 datetime으로 변환
            if isinstance(value, str):
                # 다양한 날짜 형식 지원
                for fmt in ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"]:
                    try:
                        value = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
            
            # datetime 객체가 아니면 원래 값 반환
            if not isinstance(value, datetime):
                return value
            
            # 포맷 문자열이 있으면 적용
            if format_string:
                # YYYY -> %Y, MM -> %m, DD -> %d 등으로 변환
                format_string = format_string.replace('YYYY', '%Y')
                format_string = format_string.replace('MM', '%m')
                format_string = format_string.replace('DD', '%d')
                return value.strftime(format_string)
            
            # 기본 포맷
            return value.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Date formatting error: {str(e)}", error=str(e))
            return value
    
    def render(self, document_type: str, data: Dict[str, Any]) -> str:
        """문서 데이터를 HTML로 렌더링"""
        logger.debug("Rendering document", document_type=document_type)
        
        try:
            # 문서 유형에 맞는 템플릿 파일 가져오기
            template_name = self._get_template_name(document_type)
            logger.debug("Looking for template", template_name=template_name)
            
            # 템플릿용 데이터 준비
            template_data = self._prepare_template_data(data)
            
            # 템플릿 검색 경로 출력
            search_paths = self.template_env.loader.searchpath
            logger.debug("Template search paths", paths=search_paths)
            
            template = self.template_env.get_template(template_name)
            
            # 전체 문서 렌더링
            rendered_html = template.render(**template_data)
            
            logger.debug("Document rendered successfully", document_type=document_type)
            return rendered_html
            
        except Exception as e:
            logger.error("Document rendering failed", document_type=document_type, error=str(e))
            raise RenderingError(f"Failed to render document {document_type}: {str(e)}")
    
    def _prepare_template_data(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """섹션 기반 문서 데이터를 템플릿에서 쉽게 사용할 수 있는 형태로 변환"""
        # 기본 문서 정보
        template_data = {
            "document_type": document.get("document_type", "")
        }
        
        # 메타데이터 복사
        if "metadata" in document:
            template_data["metadata"] = document["metadata"]
        
        # 각 섹션의 데이터를 섹션 타입을 키로 하여 템플릿 데이터에 추가
        for section in document.get("sections", []):
            section_type = section.get("section_type", "")
            section_data = section.get("data", {})
            
            if section_type:
                template_data[section_type] = section_data
        
        logger.debug("Prepared template data", template_data_keys=list(template_data.keys()))
        return template_data
    
    def _get_template_name(self, document_type: str) -> str:
        """문서 유형에 따른 템플릿 파일명 반환"""
        template_mapping = {
            "견적서": "estimate.html",
            "거래명세서": "trading_statement.html",
            "출장신청서": "travel_application.html",
            "출장정산신청서": "travel_expense.html",
            "회의비사용신청서": "meeting_expense.html",
            "회의록": "meeting_minutes.html",
            "구매의뢰서": "purchase_order.html",
            "전문가활용계획서": "expert_util_plan.html",
            "전문가자문확인서": "expert_consult_confirm.html",
            "지출결의서": "expenditure.html"
        }
        
        if document_type not in template_mapping:
            logger.error("Unsupported document type", document_type=document_type)
            raise RenderingError(f"Unsupported document type: {document_type}")
        
        logger.debug("Template name resolved", document_type=document_type, template=template_mapping[document_type])
        return template_mapping[document_type]
