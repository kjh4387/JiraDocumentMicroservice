from jinja2 import Template,Environment,meta
from pydantic import create_model, BaseModel
import logging

class TemplateRenderer:
    def __init__(self):
        pass
    def render(self, template_str: str, context: dict) -> str:
        template = Template(template_str)
        return template.render(**context)
    
    def extract_placeholders(template_str: str) -> BaseModel:
        """
        템플릿 문자열에서 사용된 placeholder 목록을 추출합니다.
        Args:
            template_str (str): 템플릿 문자열
        Returns:
            set: placeholder 문자열의 집합
        """
        env = Environment()
        ast = env.parse(template_str)
        return create_model("DynamicDocModel",meta.find_undeclared_variables(ast))