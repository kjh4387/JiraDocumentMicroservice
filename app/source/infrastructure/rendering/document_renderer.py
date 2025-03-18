from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from app.source.core.interfaces import DocumentRenderer, SectionRenderer
from app.source.core.exceptions import RenderingError
from app.source.core.logging import get_logger
import os

logger = get_logger(__name__)

class JinjaDocumentRenderer(DocumentRenderer):
    """Jinja2를 사용한 문서 렌더링 - 통합 템플릿 방식"""
    
    def __init__(self, template_dir: str):
        logger.debug("Initializing JinjaDocumentRenderer", template_dir=template_dir)
        try:
            self.template_dir = template_dir
            self.template_env = Environment(loader=FileSystemLoader(template_dir))
            logger.info("Document renderer initialized", template_dir=template_dir)
        except Exception as e:
            logger.error("Failed to initialize document renderer", error=str(e))
            raise RenderingError(f"Failed to initialize document renderer: {str(e)}")
    
    def render(self, document_type: str, data: Dict[str, Any]) -> str:
        """문서 데이터를 HTML로 통합 렌더링"""
        logger.debug("Rendering document", document_type=document_type)
        
        try:
            # 문서 템플릿 가져오기 - 다양한 경로 시도
            template_name = self._get_template_path(document_type)
            
            # 템플릿 렌더링 - 모든 데이터를 한 번에 전달
            template = self.template_env.get_template(template_name)
            rendered_html = template.render(
                document_type=document_type,
                **data  # 모든 데이터를 템플릿에 직접 전달
            )
            
            logger.debug("Document rendered successfully", document_type=document_type, template=template_name)
            return rendered_html
            
        except TemplateNotFound as e:
            error_msg = f"템플릿을 찾을 수 없습니다: '{document_type}', 경로: {str(e)}"
            logger.error("Template not found", document_type=document_type, error=str(e))
            raise RenderingError(error_msg)
            
        except Exception as e:
            logger.error("Document rendering failed", document_type=document_type, error=str(e))
            raise RenderingError(f"문서 '{document_type}' 렌더링 실패: {str(e)}")
    
    def _get_template_path(self, document_type: str) -> str:
        """문서 유형에 맞는 템플릿 파일 경로 찾기"""
        # 우선순위별 템플릿 경로 시도
        template_paths = [
            f"{document_type}.html",                 # 직접 문서 이름 (견적서.html)
            f"documents/{document_type}.html",       # documents/ 폴더 내 문서 이름
            self._get_template_name(document_type)   # 영문 매핑 (기존 호환성)
        ]
        
        for path in template_paths:
            try:
                # 템플릿이 존재하는지 확인
                self.template_env.get_template(path)
                logger.debug("Template found", path=path)
                return path
            except TemplateNotFound:
                continue
        
        # 마지막 경로를 기본값으로 반환 (없으면 나중에 예외 발생)
        return template_paths[-1]
    
    def _get_template_name(self, document_type: str) -> str:
        """문서 유형에 맞는 템플릿 파일명 반환 (기존 매핑)"""
        mapping = {
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
        
        if document_type not in mapping:
            logger.warning("Unsupported document type, using fallback", document_type=document_type)
            return "default.html"
        
        logger.debug("Template mapping resolved", document_type=document_type, 
                    template=mapping[document_type])
        return mapping[document_type]
    
    def _generate_fallback_html(self, document_type: str, data: Dict[str, Any]) -> str:
        """템플릿을 찾지 못한 경우 기본 HTML 생성 (비상용)"""
        logger.warning("Generating fallback HTML for document", document_type=document_type)
        
        html = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>{document_type}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 20px; border: 1px solid #ddd; padding: 10px; }}
                h1 {{ color: #333; }}
                dl {{ margin: 0; }}
                dt {{ font-weight: bold; }}
                dd {{ margin-left: 20px; margin-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>{document_type}</h1>
        """
        
        # 각 데이터 섹션 추가
        for key, value in data.items():
            if key == "document_type":
                continue
                
            html += f'<div class="section">\n'
            html += f'<h2>{key}</h2>\n'
            html += self._generate_data_html(value)
            html += '</div>\n'
            
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_data_html(self, data: Any) -> str:
        """데이터를 HTML로 변환"""
        if isinstance(data, dict):
            html = "<dl>\n"
            for k, v in data.items():
                html += f"<dt>{k}</dt>\n"
                html += f"<dd>{self._generate_data_html(v)}</dd>\n"
            html += "</dl>\n"
            return html
            
        elif isinstance(data, list):
            if not data:
                return "<p>빈 목록</p>"
                
            if isinstance(data[0], dict) and all(isinstance(item, dict) for item in data):
                # 딕셔너리 목록은 테이블로 표시
                keys = data[0].keys()
                html = "<table>\n<tr>\n"
                for key in keys:
                    html += f"<th>{key}</th>\n"
                html += "</tr>\n"
                
                for item in data:
                    html += "<tr>\n"
                    for key in keys:
                        value = item.get(key, "")
                        html += f"<td>{value}</td>\n"
                    html += "</tr>\n"
                html += "</table>\n"
                return html
            else:
                # 일반 목록
                html = "<ul>\n"
                for item in data:
                    html += f"<li>{self._generate_data_html(item)}</li>\n"
                html += "</ul>\n"
                return html
                
        else:
            # 기본 텍스트
            return str(data)
