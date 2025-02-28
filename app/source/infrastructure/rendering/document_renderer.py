from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from core.interfaces import DocumentRenderer, SectionRenderer
from core.exceptions import RenderingError
from core.logging import get_logger

logger = get_logger(__name__)

class JinjaDocumentRenderer(DocumentRenderer):
    """Jinja2를 사용한 문서 렌더링"""
    
    def __init__(self, template_dir: str, section_renderer: SectionRenderer):
        logger.debug("Initializing JinjaDocumentRenderer", template_dir=template_dir)
        try:
            self.template_env = Environment(loader=FileSystemLoader(template_dir))
            self.section_renderer = section_renderer
            logger.info("Document renderer initialized", template_dir=template_dir)
        except Exception as e:
            logger.error("Failed to initialize document renderer", error=str(e))
            raise RenderingError(f"Failed to initialize document renderer: {str(e)}")
    
    def render(self, document_type: str, data: Dict[str, Any]) -> str:
        """문서 데이터를 HTML로 렌더링"""
        logger.debug("Rendering document", document_type=document_type)
        
        try:
            # 문서 템플릿 가져오기
            template_name = self._get_template_name(document_type)
            template = self.template_env.get_template(template_name)
            
            # 각 섹션 렌더링
            rendered_sections = {}
            for section_name, section_data in data.items():
                # document_type은 섹션이 아니므로 건너뛰기
                if section_name == "document_type":
                    continue
                    
                # 딕셔너리나 리스트 타입의 데이터만 섹션으로 처리
                if isinstance(section_data, (dict, list)):
                    rendered_sections[section_name] = self.section_renderer.render_section(
                        document_type, section_name, {section_name: section_data}
                    )
            
            # 전체 문서 렌더링
            rendered_html = template.render(
                document_type=document_type,
                data=data,
                sections=rendered_sections
            )
            
            logger.debug("Document rendered successfully", document_type=document_type)
            return rendered_html
            
        except Exception as e:
            logger.error("Document rendering failed", document_type=document_type, error=str(e))
            raise RenderingError(f"Failed to render document {document_type}: {str(e)}")
    
    def _get_template_name(self, document_type: str) -> str:
        """문서 유형에 맞는 템플릿 파일명 반환"""
        mapping = {
            "견적서": "documents/estimate.html",
            "거래명세서": "documents/trading_statement.html",
            "출장신청서": "documents/travel_application.html",
            "출장정산신청서": "documents/travel_expense.html",
            "회의비사용신청서": "documents/meeting_expense.html",
            "회의록": "documents/meeting_minutes.html",
            "구매의뢰서": "documents/purchase_order.html",
            "전문가활용계획서": "documents/expert_util_plan.html",
            "전문가자문확인서": "documents/expert_consult_confirm.html",
            "지출결의서": "documents/expenditure.html"
        }
        
        if document_type not in mapping:
            logger.error("Unsupported document type", document_type=document_type)
            raise RenderingError(f"Unsupported document type: {document_type}")
        
        logger.debug("Template name resolved", document_type=document_type, template=mapping[document_type])
        return mapping[document_type]
