import os
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
import jinja2
from app.source.core.interfaces import SectionRenderer
from app.source.core.exceptions import RenderingError
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class JinjaSectionRenderer(SectionRenderer):
    """Jinja2를 사용한 섹션 렌더링"""
    
    def __init__(self, template_dir: str):
        logger.debug("Initializing JinjaSectionRenderer", template_dir=template_dir)
        try:
            self.template_env = Environment(loader=FileSystemLoader(template_dir))
            logger.info("Jinja environment initialized", template_dir=template_dir)
        except Exception as e:
            logger.error("Failed to initialize Jinja environment", error=str(e))
            raise RenderingError(f"Failed to initialize Jinja environment: {str(e)}")
    
    def render_section(self, document_type: str, section_name: str, section_data: Dict[str, Any]) -> str:
        """특정 문서 유형의 특정 섹션을 HTML로 렌더링"""
        logger.debug("Rendering section", document_type=document_type, section_name=section_name)
        
        # 섹션별 템플릿 경로 생성
        template_path = f"sections/{section_name}/{document_type}.html"
        template_search_path = self.template_env.loader.searchpath[0]
        
        # 해당 섹션 템플릿이 없으면 기본 템플릿 사용
        if not os.path.exists(os.path.join(template_search_path, template_path)):
            logger.debug("Section-specific template not found, using default template", 
                        document_type=document_type, section_name=section_name)
            template_path = f"sections/{section_name}/default.html"
        
        try:
            template = self.template_env.get_template(template_path)
            rendered_html = template.render(**section_data)
            logger.debug("Section rendered successfully", 
                        document_type=document_type, section_name=section_name)
            return rendered_html
        except jinja2.exceptions.TemplateNotFound:
            logger.warning("Template not found, generating simple HTML", 
                          template_path=template_path)
            # 기본 템플릿도 없으면 간단한 HTML 생성
            return f"<div class='section {section_name}'>{section_data}</div>"
        except Exception as e:
            logger.error("Section rendering failed", 
                        document_type=document_type, section_name=section_name, error=str(e))
            raise RenderingError(f"Failed to render section {section_name}: {str(e)}")
