# doc-gen-service/app/gen.py

from fastapi import FastAPI, Body
from pydantic import BaseModel
import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import uuid

app = FastAPI()

class DocData(BaseModel):
    title: str
    content: str

@app.post("/generate-pdf")
def generate_pdf(data: DocData):
    """
    템플릿 + 주어진 data -> PDF 생성
    """
    # 템플릿 로드
    template_path = os.path.join(os.getcwd(), "templates")
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template("example_template.html")

    # HTML 렌더링
    html_content = template.render(title=data.title, content=data.content)

    # PDF 파일명 생성
    output_filename = f"generated_{uuid.uuid4()}.pdf"
    output_path = os.path.join("/app/generated", output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # WeasyPrint로 PDF 생성
    HTML(string=html_content).write_pdf(output_path)

    return {
        "pdf_path": output_path,
        "message": "PDF generated successfully"
    }

@app.get("/")
def read_root():
    return {"message": "Doc-Gen service is running"}
