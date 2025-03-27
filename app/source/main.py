import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional
from application.dto.document_dto import DocumentRequestDTO, DocumentResponseDTO
from config.settings import get_settings
from config.di_container import DIContainer
from core.exceptions import DocumentAutomationError, RenderingError
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# FastAPI 앱 인스턴스 생성
app = FastAPI()
container: Optional[DIContainer] = None

def get_container() -> DIContainer:
    if container is None:
        raise RuntimeError("Container not initialized")
    return container

# 로깅 설정
def setup_logging(level: str = "INFO") -> logging.Logger:
    """로깅 설정
    
    Args:
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        설정된 로거 인스턴스
    """
    # 루트 로거 설정
    root_logger = logging.getLogger()
    
    # 로깅 레벨 설정
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # 포맷터 설정
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 스트림 핸들러 설정
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    
    # 다른 로거들의 레벨도 설정
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.setLevel(numeric_level)
        
    return root_logger

def load_config() -> Dict[str, Any]:
    """설정 로드"""
    config = {
        "schema_path": os.path.join("app", "source", "schemas", "IntegratedDocumentSchema.json"),
        "template_dir": os.path.join("app", "source", "templates"),
        "output_dir": os.path.join("output"),
        "database": {
            "host": os.environ.get("DB_HOST", "db"),
            "port": int(os.environ.get("DB_PORT", 5432)),
            "user": os.environ.get("DB_USER", "myuser"),
            "password": os.environ.get("DB_PASSWORD", "mypassword"),
            "database": os.environ.get("DB_NAME", "mydb")
        },
        "jira": {
            "base_url": os.environ.get("JIRA_BASE_URL"),
            "username": os.environ.get("JIRA_USERNAME"),
            "api_token": os.environ.get("JIRA_API_TOKEN"),
            "download_dir": os.path.join("downloads"),
            "field_mapping_source": "api"  # or "file"
        }
    }
    return config

def process_jira_issue(container: DIContainer, issue_key: str) -> Optional[Dict[str, Any]]:
    """Jira 이슈 처리 및 문서 생성
    
    Args:
        container: DI 컨테이너
        issue_key: Jira 이슈 키
        
    Returns:
        생성된 문서 정보 또는 None
    """
    logger = container.logger
    try:
        # Jira 이슈 데이터 가져오기
        logger.info("Fetching Jira issue: %s", issue_key)
        jira_data = container.jira_client.get_issue(issue_key)
        
        # 첨부 파일 다운로드
        logger.info("Downloading attachments for issue: %s", issue_key)
        downloaded_files = container.jira_client.download_attachments(issue_key)
        logger.info("Downloaded %d attachments", len(downloaded_files))
        
        # Jira 데이터를 문서 데이터로 매핑
        logger.info("Mapping Jira data to document data")
        document_data = container.jira_document_mapper.preprocess_fields(jira_data)
        
        # 문서 생성
        logger.info(f"Creating document for issue: {issue_key}")
        result = container.document_service.create_document(document_data)
        
        # PDF 저장
        output_path = os.path.join(
            container.config["output_dir"],
            f"{issue_key}_{result['document_type']}.pdf"
        )
        saved_path = container.document_service.save_pdf(result["pdf"], output_path)
        logger.info("Document saved to: %s", saved_path)
        
        return result
        
    except Exception as e:
        logger.error("Error processing Jira issue %s: %s", issue_key, str(e), exc_info=True)
        return None

def main():
    """메인 함수"""
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description="Jira 이슈에서 문서 생성")
    parser.add_argument("issue_key", help="Jira 이슈 키 (예: ACCO-74)")
    parser.add_argument("--output-dir", help="출력 디렉토리 경로")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="로깅 레벨 설정")
    args = parser.parse_args()
    
    try:
        # 로깅 설정
        logger = setup_logging(args.log_level)
        logger.info("Starting document generation with log level: %s", args.log_level)
        
        # 설정 로드
        config = load_config()
        
        # 출력 디렉토리 설정
        if args.output_dir:
            config["output_dir"] = args.output_dir
        
        # 출력 디렉토리 생성
        os.makedirs(config["output_dir"], exist_ok=True)
        
        # DI 컨테이너 초기화
        container = DIContainer(config, logger)
        
        # Jira 이슈 처리
        result = process_jira_issue(container, args.issue_key)
        
        if result:
            logger.info("Document generation completed successfully")
            sys.exit(0)
        else:
            logger.error("Document generation failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        sys.exit(1)

@app.post("/api/documents")
async def create_document(request: DocumentRequestDTO):
    """문서 생성 API"""
    try:
        # DTO를 딕셔너리로 변환
        data = request.model_dump()
        
        # 문서 서비스 호출
        result = get_container().document_service.create_document(data)
        
        get_container().logger.debug("Result : %s", result)
        # 응답 변환 및 반환
        response = DocumentResponseDTO(
            document_id=result["document_id"],
            document_type=result["document_type"],
            created_at=result["created_at"],
            html=result.get("html"),
            pdf_url=f"/api/documents/{result['document_id']}/pdf"
        )
        
        return response
        
    except ValidationError as e:
        # 400 Bad Request - 유효하지 않은 요청
        error_detail = str(e)
        get_container().logger.warning("Validation error: %s", error_detail)
        raise HTTPException(
            status_code=400,
            detail={"message": "유효하지 않은 문서 요청", "error": error_detail}
        )
        
    except RenderingError as e:
        # 422 Unprocessable Entity - 유효한 요청이지만 처리할 수 없음
        error_detail = str(e)
        get_container().logger.error("Rendering error: %s", error_detail)
        raise HTTPException(
            status_code=422,
            detail={"message": "문서 렌더링 실패", "error": error_detail}
        )
        
    except DocumentAutomationError as e:
        # 500 Internal Server Error - 서버 오류
        error_detail = str(e)
        get_container().logger.error("Document automation error: %s", error_detail)
        raise HTTPException(
            status_code=500,
            detail={"message": "문서 생성 실패", "error": error_detail}
        )

if __name__ == "__main__":
    main()
