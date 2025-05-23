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
import base64

class JinjaDocumentRenderer(DocumentRenderer):
    """Jinja2를 사용한 문서 렌더링 - 통합 템플릿 방식"""
    
    def __init__(self, template_dir: str, static_dir: str, logger: logging.Logger = None):
        """
        Args:
            template_dir: 템플릿 디렉토리 경로
            static_dir: 정적 파일 디렉토리 경로
            logger: 로거 인스턴스
        """
        self.template_dir = template_dir
        self.static_dir = static_dir
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("Initializing JinjaDocumentRenderer with template_dir: %s", template_dir)
        
        try:
            # Jinja2 환경 설정
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
            
            # 정적 파일 URL 생성 함수 추가
            def static_url(path):
                """정적 파일 URL 생성"""
                if path is None:
                    self.logger.warning("Attempt to create static URL for None path")
                    return ""
                    
                self.logger.debug(f"Creating static URL for path: '{path}'")
                # static/ 접두어 제거 (Flask가 자동으로 /static 접두어를 추가함)
                new_path = path.replace('static/', '')
                result = f'/static/{new_path}'
                self.logger.debug(f"Generated static URL: '{result}'")
                return result
            
            # Base64 인코딩 이미지 생성 함수 추가
            def image_to_base64(path):
                """이미지를 Base64로 인코딩하여 데이터 URL 생성"""
                if path is None:
                    self.logger.warning("Attempt to create base64 image for None path")
                    return ""
                
                self.logger.debug(f"Converting image to base64: '{path}'")
                
                # 디버깅: 서명 디렉토리 내용 확인
                signature_dir = "/workspace/app/resources/signature"
                try:
                    if os.path.exists(signature_dir):
                        files = os.listdir(signature_dir)
                        self.logger.debug(f"Files in signature directory: {files}")
                except Exception as e:
                    self.logger.warning(f"Error listing signature directory: {str(e)}")
                
                # 서명 이미지 경로 특별 처리
                if 'signature' in path or path.endswith('.png'):
                    # 파일명만 있는 경우 (예: '김자현.png')
                    if '/' not in path:
                        self.logger.debug(f"Signature file name only, adding path: '{path}'")
                        path = f"signature/{path}"
                
                # 가능한 경로 목록
                possible_paths = [
                    path,
                    os.path.join('/app/resources', path),
                    os.path.join('/workspace/app/resources', path),
                    # 서명 파일을 위한 추가 경로
                    os.path.join('/app/resources/signature', os.path.basename(path)),
                    os.path.join('/workspace/app/resources/signature', os.path.basename(path)),
                ]
                
                # 경로에서 'static/' 접두어 제거 버전 추가
                cleaned_paths = []
                for p in possible_paths:
                    cleaned_paths.append(p.replace('static/', ''))
                possible_paths.extend(cleaned_paths)
                
                self.logger.debug(f"Checking paths: {possible_paths}")
                
                for img_path in possible_paths:
                    try:
                        # 경로 정규화
                        norm_path = os.path.normpath(img_path)
                        self.logger.debug(f"Checking path: {norm_path}")
                        
                        if os.path.exists(norm_path):
                            self.logger.debug(f"Path exists: {norm_path}")
                            if os.path.isfile(norm_path):
                                self.logger.debug(f"Image file found at: {norm_path}")
                                try:
                                    with open(norm_path, 'rb') as img_file:
                                        encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                                        
                                        # 이미지 유형 감지 (확장자 기반)
                                        file_ext = os.path.splitext(norm_path)[1].lower()
                                        if file_ext == '.png':
                                            mime_type = 'image/png'
                                        elif file_ext in ['.jpg', '.jpeg']:
                                            mime_type = 'image/jpeg'
                                        elif file_ext == '.gif':
                                            mime_type = 'image/gif'
                                        else:
                                            mime_type = 'image/png'  # 기본값
                                        
                                        result = f"data:{mime_type};base64,{encoded_string}"
                                        self.logger.debug(f"Successfully created base64 image from {norm_path}")
                                        return result
                                except Exception as e:
                                    self.logger.warning(f"Error reading file {norm_path}: {str(e)}")
                            else:
                                self.logger.debug(f"Path exists but is not a file: {norm_path}")
                        else:
                            self.logger.debug(f"Path does not exist: {norm_path}")
                    except Exception as e:
                        self.logger.warning(f"Error checking path {img_path}: {str(e)}")
                
                # 파일 찾을 수 없는 경우 대체 이미지 사용
                self.logger.warning(f"Could not find valid image file at any path for {path}")
                
                # 직접 서명 디렉토리에서 파일 이름만으로 찾기 시도
                basename = os.path.basename(path)
                signature_dir = "/workspace/app/resources/signature"
                if os.path.exists(signature_dir):
                    try:
                        files = os.listdir(signature_dir)
                        self.logger.debug(f"Looking for {basename} in {files}")
                        for file in files:
                            if file == basename:
                                filepath = os.path.join(signature_dir, file)
                                self.logger.debug(f"Found exact match: {filepath}")
                                with open(filepath, 'rb') as img_file:
                                    encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                                    return f"data:image/png;base64,{encoded_string}"
                    except Exception as e:
                        self.logger.warning(f"Error finding file in signature directory: {str(e)}")
                        
                return ""
            
            self.template_env.globals['static_url'] = static_url
            self.template_env.globals['image_to_base64'] = image_to_base64
            
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
            
            # 템플릿 렌더링
            template = self.template_env.get_template(template_name)
            self.logger.debug("Template loaded successfully")
            
            try:
                self.logger.debug("Rendering template with context")
                rendered_html = template.render(**template_context)
                self.logger.debug("Template rendered successfully")
            except Exception as template_error:
                self.logger.error("Template rendering error: %s", 
                                str(template_error), exc_info=True)
                self._debug_template_context(template_context)
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
    
    def _debug_template_context(self, template_context):
        """템플릿 컨텍스트 디버깅"""
        # 문제가 있는 변수 식별
        for key, value in template_context.items():
            if key != 'jira':  # 큰 객체 건너뛰기
                try:
                    self.logger.debug("Testing context key: %s = %r", key, value)
                    # 이 변수만으로 간단한 템플릿 렌더링 시도
                    test_template = self.template_env.from_string("{{ " + key + " }}")
                    test_template.render(**{key: value})
                except Exception as e:
                    self.logger.error("Problem with context key %s: %s", key, str(e))
    
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