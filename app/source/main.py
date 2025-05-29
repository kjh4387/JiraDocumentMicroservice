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
from flask_cors import CORS
import logging.handlers
from datetime import datetime
import shutil
from enum import Enum
from pathlib import Path

class DocumentStrategyType(Enum):
    GENERATION = "generation"  # 문서 생성
    DOWNLOAD = "download"     # 문서 다운로드



def create_flask_app(config: dict, logger: logging.Logger) -> Flask:
    """Flask 인스턴스를 설정값으로 생성하고 CORS 등 부가 설정을 적용."""
    app = Flask(
        __name__,
        static_folder=config["static_dir"],      # 디스크 절대경로
        static_url_path="/static",
        template_folder=config["template_dir"],
    )

    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["*"],
        }
    })

    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.logger = logger                       
    return app

container: Optional[DIContainer] = None

def get_container() -> DIContainer:
    if container is None:
        raise RuntimeError("Container not initialized")
    return container

# 로깅 설정
def setup_logging(level: str = "INFO", log_dir_env: Optional[str] = None) -> logging.Logger:
    """안전한 로깅 초기화
    - 상대경로 → 절대경로 통일
    - logs 디렉터리 없으면 자동 생성, 권한 오류 있으면 콘솔만 사용
    - 중복 핸들러 방지
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # 2) 로그 저장 디렉터리 결정
    base_dir = Path(__file__).resolve().parent        # 프로젝트 루트(이 파일 기준)
    log_dir  = Path(log_dir_env) if log_dir_env else base_dir / "logs"

    # 3) 중복 핸들러 제거 (재호출 대비)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for h in list(root_logger.handlers):
            root_logger.removeHandler(h)
            h.close()

    root_logger.setLevel(numeric_level)

    # 4) 공통 포맷터
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # 5) 콘솔 스트림 핸들러 (항상)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(numeric_level)
    root_logger.addHandler(sh)

    # 6) 파일 핸들러 (권한·디렉터리 체크)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"app_{datetime.now():%Y%m%d}.log"

        fh = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        fh.setLevel(numeric_level)
        root_logger.addHandler(fh)
        root_logger.info("File logging → %s", log_file)

    except PermissionError as e:
        # 쓰기 권한 없으면 파일 핸들러 생략하고 경고만 출력
        root_logger.warning("Cannot write logs to %s (%s) — falling back to console only", log_dir, e)

    return root_logger

def load_config() -> Dict[str, Any]:
    """설정 로드"""
    config = {
        "schema_path": os.path.join("app", "source", "schemas", "IntegratedDocumentSchema.json"),
        "template_dir": os.path.join("app", "source", "templates"),
        "static_dir": os.path.abspath(os.path.join("app", "resources")),
        "output_dir": os.path.join("output/Paperworks/Paperworks/00. 연구비 증빙서류"),
        "dir_name_format": "{research_project}/{parent_issue_subject}/{date}_{parent_issue_key}_{parent_issue_summary}",
        "file_name_format": "{summary}",
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

def process_jira_issue_with_data(container: DIContainer, issue_data: dict) -> Optional[Dict[str, Any]]:
    """Jira 이슈 데이터 처리"""
    logger = container.logger
    jira_data = issue_data
    issue_key = jira_data['key']
    # Jira의 custom field 부분을 필드명으로 매핑
    mapped_jira_data = container.jira_client.map_issue(jira_data)
    
    logger.info("Mapping Jira data to document data")
    # Jira 데이터 preprocess
    document_data = container.jira_document_mapper.preprocess_fields(mapped_jira_data)

    document_type = container.document_service.get_document_type(document_data)
    document_data['document_type'] = document_type
    logger.info(f"Document type: {document_type}")


    # 문서 생성
    result = container.document_service.create_document(document_data, document_type)
    
    # 디버깅을 위한 파일 저장
    #if logger.isEnabledFor(logging.DEBUG):
    #    output_path = os.path.join(
    #        container.config['output_dir'],
    #        f"{issue_key}_{result['document_type']}.pdf"
    #    )
    #    # 기존 파일이 존재하면 삭제
    #    if os.path.exists(output_path):
    #       os.remove(output_path)
    #    shutil.copy(result['full_path'], output_path)
    #    logger.info("Document saved to: %s", output_path)
    
    process_save_document(document_data, result)
    # PDF 바이트 데이터를 제외한 응답 생성
    response_data = {
        "document_type": result['document_type'],
        "issue_key": issue_key,
        "status": "success"
    }
    
    return response_data

    #except Exception as e:
    #    logger.error(f"Error processing Jira issue {str(e)}")
    #    return None

def sanitize_folder_name(name: str) -> str:
    """폴더명으로 사용할 수 없는 특수문자를 제거하거나 대체합니다.
    
    Args:
        name: 원본 폴더명
        
    Returns:
        str: 안전한 폴더명
    """
    # 윈도우/리눅스/맥에서 사용할 수 없는 문자들
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    for char in invalid_chars:
        name = name.replace(char, '_')
    # 연속된 언더스코어를 하나로 통합
    name = '_'.join(filter(None, name.split('_')))
    # 마지막에 있는 점(.) 제거
    name = name.rstrip('.')
    return name

def _get_document_path(issue_data: dict) -> str:
    """문서 저장 경로 결정"""
    # config의 dir_name_format을 사용하여 디렉토리 경로 생성
    dir_path = container.config['dir_name_format'].format(
        research_project=f"({issue_data['fields']['연구과제_선택_key']['project_code']}){sanitize_folder_name(issue_data['fields']['연구과제_선택_key']['project_name'])}",
        parent_issue_subject=issue_data['fields']['parent']['fields']['issuetype']['name'],
        date=issue_data['fields']['증빙_일자'],
        parent_issue_key=issue_data['fields']['parent']['key'],
        parent_issue_summary=issue_data['fields']['parent']['fields']['summary']
    )
    logger = container.logger
    logger.debug(f"dir_path: {dir_path}")
    return os.path.join(container.config['output_dir'], dir_path)

def _get_document_name(issue_data: dict, extension: str = "pdf") -> str:
    """문서 이름 결정"""

    name = container.config['file_name_format'].format(
        summary=issue_data['fields']['summary']
    )
    logger = container.logger
    logger.debug(f"name: {name}")
    return f"{name}.{extension}"

def process_jira_issue(container: DIContainer, issue_key: str) -> Optional[Dict[str, Any]]:
    """Jira 이슈 처리 및 문서 생성
    
    Args:
        container: DI 컨테이너
        issue_key: Jira 이슈 키
        
    Returns:
        생성된 문서 정보 또는 None
    """
    logger = container.logger
    # Jira 이슈 데이터 가져오기
    logger.info("Fetching Jira issue: %s", issue_key)
    jira_data = container.jira_client.get_issue(issue_key)
    logger.debug(f"Jira issue data: {jira_data}")
    result = process_jira_issue_with_data(container, jira_data)
    return result
        
    #except Exception as e:
    #    logger.error("Error processing Jira issue")
    #    return None
    

#TODO: 문서 저장 경로 추출, 문서 저장 처리(jira 이슈에 첨부, sharepoint 혹은 onedrive 에 저장)
def process_save_document(request_data: Dict[str, Any], result: Dict[str, Any]):
    """
    요청 데이터에서 문서 저장 경로를 추출하고, 문서를 저장합니다.
    """
    logger = container.logger
    strategy_type = result.get("strategy_type", DocumentStrategyType.GENERATION.value)
    logger.debug(f"result: {result}")
    import shutil
    from pathlib import Path
    if strategy_type == DocumentStrategyType.GENERATION.value:
        # Jira에 업로드
        container.jira_client.upload_attachment(request_data['key'], result['full_path'])
        # 생성된 PDF 파일 저장
        path = os.path.join(_get_document_path(request_data),  _get_document_name(request_data))
        logger.debug(f"path: {path}")
        # destination directory 생성
        Path(_get_document_path(request_data)).mkdir(parents=True, exist_ok=True)
        # 기존 파일이 존재하면 삭제
        if os.path.exists(path):
            os.remove(path)
        shutil.copy(result['full_path'], path)
    
    elif strategy_type == DocumentStrategyType.DOWNLOAD.value:
        # 다운로드된 파일은 이미 Jira에 있으므로 업로드 불필요
        path = os.path.join(_get_document_path(request_data),  _get_document_name(request_data, result['extension']))
        # destination directory 생성
        os.makedirs(os.path.dirname(path), exist_ok=True)
        logger.debug(f"result['file_path']: {result['file_path']}, path: {path}")
        shutil.copy2(result['full_path'], path)
    
    logger.info("Document saved to: %s", path)



log_level = os.environ.get("LOG_LEVEL", "INFO")

def initialize_app(log_level: str = "INFO") -> Flask:
    """설정 ▸ DI ▸ Flask 세 단계를 모두 초기화."""
    # 1) 로깅
    logger = setup_logging(log_level)

    # 2) 설정
    config = load_config()
    os.makedirs(config["output_dir"], exist_ok=True)

    # 3) DIContainer
    global container
    container = DIContainer(config, logger)

    # 4) Flask
    app = create_flask_app(config, logger)

    logger.info("Flask application initialized")
    return app

app: Flask = initialize_app(log_level=os.getenv("LOG_LEVEL", "INFO"))

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
            config['output_dir'] = args.output_dir
        
        # 출력 디렉토리 생성
        os.makedirs(config['output_dir'], exist_ok=True)
        
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

@app.route("/api/documents", methods=['POST'])
def create_document():
    """문서 생성 API"""
    try:
        request_data = request.get_json()
        logger = container.logger
        logger.debug("Request Headers: %s", dict(request.headers))
        logger.debug("Request Content-Type: %s", request.content_type)
        logger.debug("Request Body: %s", request.get_data(as_text=True))
            
        result = process_jira_issue_with_data(get_container(), request_data['issue'])
        
        if not result:
            return jsonify({"error": "Failed to process Jira issue"}), 500
            
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Error creating document: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug/file-check", methods=['GET'])
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
        result['full_path'] = full_path
        
        # 파일 또는 디렉토리 존재 여부 확인
        result['exists'] = os.path.exists(full_path)
        result['is_file'] = os.path.isfile(full_path) if result['exists'] else False
        result['is_dir'] = os.path.isdir(full_path) if result['exists'] else False
        
        # 여러 경로 변형 확인
        check_paths = [
            full_path,
            os.path.join("/app/resources", file_path.replace('static/', '')),
            os.path.join("/workspace/app/resources", file_path.replace('static/', '')),
            os.path.join(base_dir, "resources", file_path.replace('static/', ''))
        ]
        
        for path in check_paths:
            result['file_checks'].append({
                "path": path,
                "exists": os.path.exists(path),
                "is_file": os.path.isfile(path) if os.path.exists(path) else False,
                "is_dir": os.path.isdir(path) if os.path.exists(path) else False
            })
        
        # 디렉토리인 경우 내용 나열
        if result['is_dir']:
            try:
                files = os.listdir(full_path)
                result['directory_listing']['files'] = files
                result['directory_listing']['count'] = len(files)
            except Exception as e:
                result['directory_listing']['error'] = str(e)
        
        # 정적 파일 디렉토리 내용 나열
        try:
            static_dir = os.path.join(base_dir, "resources")
            if os.path.isdir(static_dir):
                result['static_directory'] = {
                    "path": static_dir,
                    "files": os.listdir(static_dir)[:20],  # 처음 20개만 표시
                    "count": len(os.listdir(static_dir))
                }
                
                # signature 폴더 확인
                sig_dir = os.path.join(static_dir, "signature")
                if os.path.isdir(sig_dir):
                    result['signature_directory'] = {
                        "path": sig_dir,
                        "files": os.listdir(sig_dir),
                        "count": len(os.listdir(sig_dir))
                    }
        except Exception as e:
            result['static_directory_error'] = str(e)
        
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

