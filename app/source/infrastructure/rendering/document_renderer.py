from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from app.source.core.interfaces import DocumentRenderer
from app.source.core.exceptions import RenderingError
import logging
from app.source.infrastructure.rendering.filter_util import (
    format_date, format_korean_date, format_date_range, 
    format_number, number_to_korean, format_korean_currency, format_korean_currency_with_num,
    format_currency_aligned, format_number_aligned
)
import os
from typing import Optional

class JinjaDocumentRenderer(DocumentRenderer):
    """Jinja2를 사용한 문서 렌더링 - 통합 템플릿 방식"""
    
    def __init__(self, template_dir: str, logger: logging.Logger = None):
        """
        Args:
            template_dir: 템플릿 디렉토리 경로
            logger: 로거 인스턴스
        """
        self.template_dir = template_dir
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("Initializing JinjaDocumentRenderer with template_dir: %s", template_dir)
        
        try:
            self.template_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=True
            )
            self.logger.info("Document renderer initialized with template_dir: %s", template_dir)
            
            # 커스텀 필터 등록
            self.template_env.filters['format_date'] = format_date
            self.template_env.filters['korean_date'] = format_korean_date
            self.template_env.filters['date_range'] = format_date_range
            self.template_env.filters['format_number'] = format_number
            
            # 한글 금액 필터 추가
            self.template_env.filters['korean_number'] = number_to_korean
            self.template_env.filters['korean_currency'] = format_korean_currency
            self.template_env.filters['korean_currency_with_num'] = format_korean_currency_with_num
            
            # 정렬 필터 추가
            self.template_env.filters['currency_aligned'] = format_currency_aligned
            self.template_env.filters['number_aligned'] = format_number_aligned
        except Exception as e:
            self.logger.error("Failed to initialize document renderer: %s", str(e))
            raise
    
    def render(self, document_type: str, data: Dict[str, Any]) -> str:
        """문서 데이터를 HTML로 통합 렌더링
        
        Args:
            document_type: 문서 유형 (템플릿 결정)
            data: Jira 응답 데이터 (fields 포함)
            
        Returns:
            렌더링된 HTML 문자열
        """
        self.logger.debug("Rendering document: %s", document_type)
        
        try:
            # 문서 템플릿 가져오기
            template_name = self._get_template_path(document_type)
            self.logger.debug("Using template: %s", template_name)
            
            # 템플릿에 전달할 컨텍스트 준비
            # Jira 데이터를 그대로 전달하되, 최상위 키도 접근 가능하게 함
            template_context = {
                'document_type': document_type,
            }
            
            # Jira의 fields를 최상위로 복사하여 템플릿에서 쉽게 접근 가능하게 함
            if 'fields' in data:
                self.logger.debug("Adding fields to template context")
                template_context.update(data['fields'])
            
            
            # Available keys in context for debugging
            
            # 템플릿 렌더링
            template = self.template_env.get_template(template_name)
            self.logger.debug("Template loaded successfully")
            
            try:
                self.logger.debug("Rendering template with context: %s", template_context)
                rendered_html = template.render(**template_context)
                self.logger.debug("Template rendered successfully")
            except Exception as template_error:
                self.logger.error("Template rendering error: %s", str(template_error), exc_info=True)
                # Try to identify which variable is causing the problem
                for key, value in template_context.items():
                    if key != 'jira':  # Skip large objects
                        try:
                            self.logger.debug("Testing context key: %s = %r", key, value)
                            # Try to render a simple template with just this variable
                            test_template = self.template_env.from_string("{{ " + key + " }}")
                            test_template.render(**{key: value})
                        except Exception as e:
                            self.logger.error("Problem with context key %s: %s", key, str(e))
                raise
            
            self.logger.debug("Document rendered successfully: %s, template: %s", document_type, template_name)
            return rendered_html
            
        except TemplateNotFound as e:
            error_msg = f"템플릿을 찾을 수 없습니다: '{document_type}', 경로: {str(e)}"
            self.logger.error("Template not found: %s, error: %s", document_type, str(e))
            raise RenderingError(error_msg)
            
        except Exception as e:
            self.logger.error("Document rendering failed: %s, error: %s", document_type, str(e))
            raise RenderingError(f"문서 '{document_type}' 렌더링 실패: {str(e)}")
    
    def _get_template_path(self, document_type: str) -> str:
        """문서 유형에 맞는 템플릿 파일 경로 찾기"""
        # 우선순위별 템플릿 경로 시도
        original_document_type = document_type
        template_paths = [
            f"{document_type}.html",                 # 직접 문서 이름 (견적서.html)
            f"documents/{document_type}.html",       # documents/ 폴더 내 문서 이름
            self._get_template_name(document_type)   # 영문 매핑 (기존 호환성)
        ]
        
        for path in template_paths:
            try:
                # 템플릿이 존재하는지 확인
                self.template_env.get_template(path)
                self.logger.debug("Template found: %s", path)
                return path
            except TemplateNotFound:
                self.logger.debug("Template not found: %s", path)
                continue
        
        # 어떤 템플릿도 찾지 못한 경우 모든 템플릿 목록 로깅
        try:
            all_templates = self.template_env.list_templates()
            self.logger.error("No template found for document_type: %s. Available templates: %s", 
                            original_document_type, all_templates)
            
            # 기본 템플릿 시도 (default.html)
            if "default.html" in all_templates:
                self.logger.info("Using default.html as fallback template")
                return "default.html"
                
            # 첫 번째 사용 가능한 템플릿 사용
            if all_templates:
                self.logger.info("Using first available template as fallback: %s", all_templates[0])
                return all_templates[0]
        except Exception as e:
            self.logger.error("Error listing templates: %s", str(e))
        
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
            self.logger.warning("Unsupported document type, using fallback: %s", document_type)
            return "default.html"
        
        self.logger.debug("Template mapping resolved: %s -> %s", document_type, mapping[document_type])
        return mapping[document_type]
    
    
    
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