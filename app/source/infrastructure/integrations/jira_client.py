from typing import Dict, Any, List, Optional
import requests
from requests.auth import HTTPBasicAuth
import os
import json
import re
import logging
from app.source.core.interfaces import JiraClient, JiraFieldMapper
from app.source.infrastructure.mapping.jira_field_mapper import ApiJiraFieldMappingProvider, JiraFieldMapperimpl

class JiraClient(JiraClient):
    """Jira API와 통신하는 클라이언트"""
    
    def __init__(self, jira_base_url = os.getenv("JIRA_BASE_URL"), username = os.getenv("JIRA_USERNAME"), api_token = os.getenv("JIRA_API_TOKEN"), download_dir: str = None, field_mapper: Optional[JiraFieldMapper] = None, logger: logging.Logger = None):
        """JiraClient 초기화
        
        Args:
            jira_base_url (str): Jira 인스턴스 기본 URL (예: "https://yourdomain.atlassian.net")
            username (str): Jira 계정 이메일
            api_token (str): Jira API 토큰
            download_dir (str, optional): 첨부 파일 다운로드 기본 경로
            field_mapper (JiraFieldMapper, optional): Jira 필드 매퍼
            logger (logging.Logger, optional): 로거 인스턴스
        """
        self.jira_base_url = jira_base_url
        self.auth = HTTPBasicAuth(username, api_token)
        self.headers = {"Accept": "application/json"}
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        self.field_mapper = field_mapper
        self.logger = logger or logging.getLogger(__name__)
        
        # 다운로드 디렉토리 생성
        os.makedirs(self.download_dir, exist_ok=True)
        
        self.logger.debug("JiraClient initialized with base URL: %s", jira_base_url)

    def map_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """이슈 데이터 처리
        
        Args:
            issue_data (Dict[str, Any]): 원본 이슈 데이터
            
        Returns:
            Dict[str, Any]: 커스텀 필드 매핑 처리된 이슈 데이터
        """
        if self.field_mapper:
            data = self.field_mapper.transform_response(issue_data)
            
            return data
        else:
            self.logger.error("Field mapper is not set.")
            raise Exception("Field mapper is not set")

    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """이슈 정보 조회
        
        Args:
            issue_key (str): 이슈 키 (예: "PROJ-123")
            
        Returns:
            Dict[str, Any]: 이슈 정보
            
        Raises:
            Exception: API 호출 실패 시
        """
        issue_url = f"{self.jira_base_url}/rest/api/2/issue/{issue_key}"
        response = requests.get(issue_url, headers=self.headers, auth=self.auth)
        
        if response.status_code == 200:
            self.logger.info(f"Successfully fetched issue: {issue_key}")
            data = response.json()
            
            # 필드 매퍼가 설정된 경우 응답 변환
            if self.field_mapper:
                data = self.field_mapper.transform_response(data)
            
            return data
        else:
            error_msg = f"Failed to fetch issue {issue_key}: {response.status_code} - {response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
    
    
    def download_attachments(self, issue_key: str, destination_dir: str = None) -> List[str]:
        """이슈 첨부 파일 다운로드
        
        Args:
            issue_key (str): 이슈 키 (예: "PROJ-123")
            destination_dir (str, optional): 다운로드 경로 (지정하지 않으면 기본 경로 사용)
            
        Returns:
            List[str]: 다운로드된 파일 경로 목록
        """
        issue_data = self.get_issue(issue_key)
        issue_summary = issue_data["fields"]["summary"]
        attachments = issue_data["fields"]["attachment"]
        
        if not attachments:
            self.logger.info(f"No attachments found for issue {issue_key}.")
            return []
        
        # 저장 디렉토리 결정
        folder_name = self._clean_folder_name(f"{issue_key} - {issue_summary}")
        save_dir = destination_dir or os.path.join(self.download_dir, folder_name)
        os.makedirs(save_dir, exist_ok=True)
        
        # 첨부 파일 다운로드
        downloaded_files = []
        for attachment in attachments:
            attachment_url = attachment["content"]
            file_name = attachment["filename"]
            save_path = os.path.join(save_dir, file_name)
            
            try:
                self._download_file(attachment_url, save_path)
                downloaded_files.append(save_path)
            except Exception as e:
                self.logger.error(f"Failed to download attachment {file_name}: {str(e)}")
        
        return downloaded_files
    
    def get_issue_fields(self, issue_key: str, fields: List[str] = None) -> Dict[str, Any]:
        """특정 이슈의 필드 값 조회
        
        Args:
            issue_key (str): 이슈 키 (예: "PROJ-123")
            fields (List[str], optional): 가져올 필드 이름 목록 (없으면 모든 필드 반환)
            
        Returns:
            Dict[str, Any]: 필드 이름과 값으로 구성된 딕셔너리
        """
        issue_data = self.get_issue(issue_key)
        issue_fields = issue_data["fields"]
        
        if not fields:
            return issue_fields
        
        # 요청된 필드만 추출
        result = {}
        for field in fields:
            if field in issue_fields:
                result[field] = issue_fields[field]
            else:
                self.logger.warning(f"Field '{field}' not found in issue {issue_key}")
        
        return result
    
    def _clean_folder_name(self, folder_name: str) -> str:
        """폴더명에서 유효하지 않은 문자 제거
        
        Args:
            folder_name (str): 원본 폴더명
            
        Returns:
            str: 정리된 폴더명
        """
        invalid_chars = r'[<>:"/\\|?*]'
        clean_name = re.sub(invalid_chars, '', folder_name).strip()
        return clean_name
    
    def _download_file(self, url: str, save_path: str) -> None:
        """파일 다운로드
        
        Args:
            url (str): 다운로드 URL
            save_path (str): 저장 경로
            
        Raises:
            Exception: 다운로드 실패 시
        """
        response = requests.get(url, headers=self.headers, auth=self.auth, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                file.write(response.content)
            self.logger.debug(f"File downloaded: {save_path}")
        else:
            error_msg = f"Failed to download file: {response.status_code} - {response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _make_request(self, method: str, path: str, data=None) -> Any:
        """API 요청 메서드
        
        Args:
            method (str): HTTP 메서드 (GET, POST 등)
            path (str): API 경로
            data (dict, optional): 요청 데이터
            
        Returns:
            Any: API 응답 데이터
            
        Raises:
            Exception: API 호출 실패 시
        """
        url = f"{self.jira_base_url}{path}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, auth=self.auth, json=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, auth=self.auth, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code >= 200 and response.status_code < 300:
                return response.json() if response.content else None
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            self.logger.error(f"Error making API request: {str(e)}")
            raise


    def upload_attachment(self, issue_key: str, file_path: str) -> Dict[str, Any]:
        """이슈에 첨부 파일 업로드
        
        Args:
            issue_key (str): 이슈 키 (예: "PROJ-123")
            file_path (str): 업로드할 파일 경로
            
        Returns:
            Dict[str, Any]: 업로드 결과 응답 데이터
            
        Raises:
            Exception: 업로드 실패 시
        """
        upload_url = f"{self.jira_base_url}/rest/api/2/issue/{issue_key}/attachments"
        headers = {
            **self.headers,
            "X-Atlassian-Token": "no-check"  # Jira 첨부 파일 업로드 시 필요
        }
        
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}
                response = requests.post(
                    upload_url,
                    headers=headers,
                    auth=self.auth,
                    files=files
                )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully uploaded {file_path} to {issue_key}")
                return response.json()
            else:
                error_msg = f"Failed to upload attachment: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
                
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        except Exception as e:
            self.logger.error(f"Error during file upload: {str(e)}")
            raise


# 사용 예시
if __name__ == "__main__":
    # 환경 변수나 설정 파일에서 가져오는 것이 더 안전함
    JIRA_URL = os.getenv("JIRA_BASE_URL")
    JIRA_USER = os.getenv("JIRA_USERNAME")
    JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

    # 필드 매핑 제공자 초기화   
    mapping_provider = ApiJiraFieldMappingProvider(JiraClient(JIRA_URL, JIRA_USER, JIRA_TOKEN))
    field_mapper = JiraFieldMapperimpl(mapping_provider)
    
    client = JiraClient(JIRA_URL, JIRA_USER, JIRA_TOKEN, field_mapper=field_mapper)
    
    issue_key = input("Enter the issue key (e.g., ACCO-16): ").strip()
    
    # 이슈 정보 가져오기
    issue_data = client.get_issue(issue_key)
    fields = issue_data["fields"]
    for field in fields:
        print(f"{field}: {fields[field]}")
    
    # 첨부 파일 다운로드
    downloaded_files = client.download_attachments(issue_key)
    print(f"Downloaded {len(downloaded_files)} files")
