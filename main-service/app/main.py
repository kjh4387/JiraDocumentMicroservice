# main-service/app/main.py

from fastapi import FastAPI, Body
import requests

app = FastAPI()

@app.post("/process-document")
def process_document(data: dict = Body(...)):
    """
    1) doc-gen-service에 문서 생성 요청
    2) 생성된 문서를 post-service로 전송 요청
    3) 최종 결과를 반환
    """
    doc_gen_url = "http://doc-gen-service:8001/generate-pdf"
    post_url = "http://post-service:8002/post-document"

    # 1) 문서 생성 요청
    gen_resp = requests.post(doc_gen_url, json=data)
    if gen_resp.status_code != 200:
        return {"error": "Failed to generate document"}

    # doc-gen-service로부터 생성된 PDF 경로를 받았다고 가정
    pdf_info = gen_resp.json()  # e.g., {"pdf_path": "/app/generated/example.pdf"}

    # 2) post-service에 업로드 요청
    post_resp = requests.post(post_url, json=pdf_info)
    if post_resp.status_code != 200:
        return {"error": "Failed to post document to external system"}

    return {
        "message": "Document processed successfully",
        "doc_gen_result": pdf_info,
        "post_result": post_resp.json()
    }

@app.get("/")
def read_root():
    return {"message": "Main service is running"}
