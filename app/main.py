from fastapi import FastAPI
import uvicorn
from app.source.interfaces.rest.controllers import router as document_router
from app.source.infrastructure.db_client import get_db_client
from app.source.application.bootstrap import create_document_service
from app.source.core.logging import configure_logging
from app.source.interfaces.rest.dependencies import init_dependencies

# 로깅 설정
configure_logging()

# 앱 생성
app = FastAPI(title="문서 처리 시스템")

# 초기화
db_client = get_db_client()
document_service = create_document_service(db_client)
init_dependencies(document_service)

# 라우터 등록
app.include_router(document_router)

@app.get("/")
async def root():
    return {"message": "문서 처리 시스템이 실행 중입니다."}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 