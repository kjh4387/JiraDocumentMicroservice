import requests
from requests.auth import HTTPBasicAuth
import os
import json
import re
import logging
import sys
from datetime import datetime

# 로깅 설정
log_dir = "/tmp/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"jira_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 검증
required_env_vars = ['JIRA_BASE_URL', 'JIRA_API_TOKEN', 'JIRA_USERNAME', 'JIRA_DOWNLOAD_DIR']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please set all required environment variables before running this script.")
    sys.exit(1)

# Jira 정보
try:
    jira_base_url = os.environ['JIRA_BASE_URL']
    auth_token = os.environ['JIRA_API_TOKEN']
    jira_username = os.environ['JIRA_USERNAME']
    auth = HTTPBasicAuth(jira_username, auth_token)
    
    logger.info(f"Jira configuration loaded. Base URL: {jira_base_url}, Username: {jira_username}")
except Exception as e:
    logger.error(f"Error setting up Jira configuration: {str(e)}")
    sys.exit(1)

# 헤더
headers = {
    "Accept": "application/json"
}

# 저장할 경로
try:
    download_dir = os.environ['JIRA_DOWNLOAD_DIR']
    logger.info(f"Download directory set to: {download_dir}")
    
    # 다운로드 디렉토리 존재 확인 및 생성
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        logger.info(f"Created download directory: {download_dir}")
except Exception as e:
    logger.error(f"Error setting up download directory: {str(e)}")
    sys.exit(1)

# 유효하지 않은 문자를 제거해 폴더명을 정리하는 함수
def clean_folder_name(folder_name):
    logger.debug(f"Cleaning folder name: {folder_name}")
    invalid_chars = r'[<>:"/\\|?*]'
    clean_name = re.sub(invalid_chars, '', folder_name).strip()
    logger.debug(f"Cleaned folder name: {clean_name}")
    return clean_name

# 폴더를 생성하는 함수
def create_directory(directory_path):
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.info(f"Directory created: {directory_path}")
    except Exception as e:
        logger.error(f"Error while creating directory: {str(e)}")
        raise

# 파일 다운로드 함수
def download_file(url, save_path):
    logger.info(f"Downloading file from {url} to {save_path}")
    try:
        response = requests.get(url, headers=headers, auth=auth, stream=True)
        logger.debug(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                file.write(response.content)
            file_size = os.path.getsize(save_path)
            logger.info(f"File downloaded successfully: {save_path} ({file_size} bytes)")
            return True
        else:
            logger.error(f"Failed to download file: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception during file download: {str(e)}")
        return False

# 특정 이슈의 첨부파일을 다운로드하는 함수
def fetch_attachments(issue_key):
    logger.info(f"Fetching attachments for issue: {issue_key}")
    
    try:
        issue_url = f"{jira_base_url}/rest/api/2/issue/{issue_key}"
        logger.debug(f"Issue URL: {issue_url}")
        
        response = requests.get(issue_url, headers=headers, auth=auth)
        logger.debug(f"Issue API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            issue_summary = data["fields"]["summary"]
            logger.info(f"Issue found: {issue_key} - {issue_summary}")
            
            attachments = data["fields"]["attachment"]
            logger.info(f"Found {len(attachments)} attachments")
            
            if not attachments:
                logger.warning(f"No attachments found for issue {issue_key}.")
                return []
            
            # 폴더 경로 생성
            folder_name = clean_folder_name(f"{issue_key} - {issue_summary}")
            save_dir = os.path.join(download_dir, folder_name)
            create_directory(save_dir)
            
            # 첨부파일 다운로드
            downloaded_files = []
            for i, attachment in enumerate(attachments, 1):
                attachment_url = attachment["content"]
                file_name = attachment["filename"]
                save_path = os.path.join(save_dir, file_name)
                
                logger.info(f"Downloading attachment {i}/{len(attachments)}: {file_name}")
                success = download_file(attachment_url, save_path)
                
                if success:
                    downloaded_files.append(save_path)
            
            logger.info(f"Downloaded {len(downloaded_files)}/{len(attachments)} files for issue {issue_key}")
            return downloaded_files
        else:
            logger.error(f"Failed to fetch issue details: {response.status_code} - {response.text}")
            return []
    except KeyError as e:
        logger.error(f"Key error while processing issue data: {str(e)}")
        logger.debug("Response data structure might be different than expected")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching attachments: {str(e)}")
        return []

# 실행 부분
if __name__ == "__main__":
    try:
        logger.info("Starting Jira file download script")
        # 수정: 적절한 입력 프롬프트로 변경
        issue_key = input("Enter the issue key (e.g., ACCO-16): ").strip()
        logger.info(f"Processing issue: {issue_key}")
        
        if not issue_key:
            logger.error("No issue key provided. Exiting.")
            sys.exit(1)
        
        downloaded_files = fetch_attachments(issue_key)
        
        if downloaded_files:
            logger.info(f"Successfully downloaded {len(downloaded_files)} files:")
            for file_path in downloaded_files:
                logger.info(f" - {file_path}")
        else:
            logger.warning("No files were downloaded.")
        
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")
        sys.exit(1)