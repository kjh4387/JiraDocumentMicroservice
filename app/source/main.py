import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional
from app.source.application.dto.document_dto import DocumentRequestDTO, DocumentResponseDTO
from app.source.config.settings import get_settings
from app.source.config.di_container import DIContainer
from app.source.core.exceptions import DocumentAutomationError, RenderingError
from flask import Flask, request, jsonify, abort
from pydantic import ValidationError

# Flask 앱 인스턴스 생성
app = Flask(__name__, 
           static_folder="../resources",  # app/resources 디렉토리를 정적 파일로 제공
           template_folder="../source/templates")   # app/source/templates 디렉토리를 템플릿으로 제공

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
    
def process_save_document(request_data: Dict[str, Any], container: DIContainer, result: Dict[str, Any]):
    """
    요청 데이터에서 문서 저장 경로를 추출하고, 문서를 저장합니다.
    """
    raise NotImplementedError("Not implemented")

def initialize_app(config_path=None, log_level="INFO"):
    """Flask 앱 초기화 함수"""
    global container
    
    # 로깅 설정
    logger = setup_logging(log_level)
    logger.info("Starting Flask app with log level: %s", log_level)
    
    # 설정 로드
    config = load_config()
    
    # 출력 디렉토리 생성
    os.makedirs(config["output_dir"], exist_ok=True)
    
    # DI 컨테이너 초기화
    container = DIContainer(config, logger)
    
    # Flask 애플리케이션 추가 설정
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # 시작 로그
    logger.info("Flask application initialized successfully")
    
    return app

# 앱 초기화 - 컨테이너에서 자동 시작을 위해
initialize_app(log_level=os.environ.get("LOG_LEVEL", "INFO"))

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
        global container
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

@app.route("/api/documents", methods=["POST"])
def create_document():
    """문서 생성 API"""
    try:
        request_data = request.get_json()
        issue_key = request_data.get("issue_key")
        
        if not issue_key:
            return jsonify({"error": "Missing issue_key parameter"}), 400
            
        result = process_jira_issue(get_container(), issue_key)
        
        if not result:
            return jsonify({"error": "Failed to process Jira issue"}), 500
            
        # 저장 처리
        if "save_path" in request_data:
            process_save_document(request_data, get_container(), result)
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Error creating document: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug/file-check", methods=["GET"])
def check_files():
    """파일 시스템 디버깅 API"""
    try:
        # 디버깅 대상 경로 (쿼리 파라미터에서 가져오거나 기본값 사용)
        file_path = request.args.get("path", "")
        base_dir = request.args.get("base_dir", "/app")
        
        # 결과 저장
        result = {
            "request_info": {
                "file_path": file_path,
                "base_dir": base_dir
            },
            "file_checks": [],
            "directory_listing": {}
        }
        
        # 전체 경로 생성
        full_path = os.path.join(base_dir, file_path)
        result["full_path"] = full_path
        
        # 파일 또는 디렉토리 존재 여부 확인
        result["exists"] = os.path.exists(full_path)
        result["is_file"] = os.path.isfile(full_path) if result["exists"] else False
        result["is_dir"] = os.path.isdir(full_path) if result["exists"] else False
        
        # 여러 경로 변형 확인
        check_paths = [
            full_path,
            os.path.join("/app/resources", file_path.replace('static/', '')),
            os.path.join("/workspace/app/resources", file_path.replace('static/', '')),
            os.path.join(base_dir, "resources", file_path.replace('static/', ''))
        ]
        
        for path in check_paths:
            result["file_checks"].append({
                "path": path,
                "exists": os.path.exists(path),
                "is_file": os.path.isfile(path) if os.path.exists(path) else False,
                "is_dir": os.path.isdir(path) if os.path.exists(path) else False
            })
        
        # 디렉토리인 경우 내용 나열
        if result["is_dir"]:
            try:
                files = os.listdir(full_path)
                result["directory_listing"]["files"] = files
                result["directory_listing"]["count"] = len(files)
            except Exception as e:
                result["directory_listing"]["error"] = str(e)
        
        # 정적 파일 디렉토리 내용 나열
        try:
            static_dir = os.path.join(base_dir, "resources")
            if os.path.isdir(static_dir):
                result["static_directory"] = {
                    "path": static_dir,
                    "files": os.listdir(static_dir)[:20],  # 처음 20개만 표시
                    "count": len(os.listdir(static_dir))
                }
                
                # signature 폴더 확인
                sig_dir = os.path.join(static_dir, "signature")
                if os.path.isdir(sig_dir):
                    result["signature_directory"] = {
                        "path": sig_dir,
                        "files": os.listdir(sig_dir),
                        "count": len(os.listdir(sig_dir))
                    }
        except Exception as e:
            result["static_directory_error"] = str(e)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 앱 실행
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 명령행 실행 (CLI)
        main()
    else:
        # 웹 서버 실행
        app.run(debug=True, host="0.0.0.0", port=8000)
