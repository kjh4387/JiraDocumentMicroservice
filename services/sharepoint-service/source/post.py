# post-service/app/post.py

from fastapi import FastAPI, Body
import os
from office365.sharepoint.client_context import ClientContext
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()  # .env 로드 (SHAREPOINT_SITE, SHAREPOINT_USER, SHAREPOINT_PW 등)

@app.post("/post-document")
def post_document(payload: dict = Body(...)):
    """
    payload: { "pdf_path": "/app/generated/xxx.pdf" }
    """
    pdf_path = payload.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        return {"error": "PDF file not found"}

    # SharePoint에 업로드
    sharepoint_site = os.getenv("SHAREPOINT_SITE")
    sharepoint_user = os.getenv("SHAREPOINT_USER")
    sharepoint_pw = os.getenv("SHAREPOINT_PW")
    target_folder = os.getenv("SHAREPOINT_FOLDER", "Shared Documents")

    try:
        ctx = ClientContext(sharepoint_site).with_user_credentials(sharepoint_user, sharepoint_pw)
        with open(pdf_path, "rb") as pdf_file:
            file_content = pdf_file.read()

        file_name = os.path.basename(pdf_path)
        sp_folder = ctx.web.get_folder_by_server_relative_url(target_folder)
        sp_file = sp_folder.upload_file(file_name, file_content).execute_query()

        return {"message": f"File '{file_name}' posted to SharePoint."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"message": "Post service is running"}
