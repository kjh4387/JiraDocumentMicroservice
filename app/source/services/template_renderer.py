from jinja2 import Template

class TemplateRenderer:
    def render(self, template_str: str, context: dict) -> str:
        template = Template(template_str)
        return template.render(**context)
