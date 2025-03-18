from typing import Dict, Any, List, Optional
import requests
from requests.auth import HTTPBasicAuth
import os
import json
import re
from app.source.core.logging import get_logger
from app.source.core.interfaces import JiraClient, JiraFieldMappingProvider, JiraFieldMapper

logger = get_logger(__name__)

class JiraClient(JiraClient):
    """Jira API와 통신하는 클라이언트"""
    
    def __init__(self, jira_base_url = os.getenv("JIRA_BASE_URL"), username = os.getenv("JIRA_USERNAME"), api_token = os.getenv("JIRA_API_TOKEN"), download_dir: str = None, field_mapper: Optional[JiraFieldMapper] = None):
        """JiraClient 초기화
        
        Args:
            jira_base_url (str): Jira 인스턴스 기본 URL (예: "https://yourdomain.atlassian.net")
            username (str): Jira 계정 이메일
            api_token (str): Jira API 토큰
            download_dir (str, optional): 첨부 파일 다운로드 기본 경로
            field_mapper (JiraFieldMapper, optional): Jira 필드 매퍼
        """
        self.jira_base_url = jira_base_url
        self.auth = HTTPBasicAuth(username, api_token)
        self.headers = {"Accept": "application/json"}
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        self.field_mapper = field_mapper
        
        # 다운로드 디렉토리 생성
        os.makedirs(self.download_dir, exist_ok=True)
        
        logger.debug(f"JiraClient initialized with base URL: {jira_base_url}")
    
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
            logger.info(f"Successfully fetched issue: {issue_key}")
            data = response.json()
            
            # 필드 매퍼가 설정된 경우 응답 변환
            if self.field_mapper:
                data = self.field_mapper.transform_response(data)
            
            return data
        else:
            error_msg = f"Failed to fetch issue {issue_key}: {response.status_code} - {response.text}"
            logger.error(error_msg)
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
            logger.info(f"No attachments found for issue {issue_key}.")
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
                logger.error(f"Failed to download attachment {file_name}: {str(e)}")
        
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
                logger.warning(f"Field '{field}' not found in issue {issue_key}")
        
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
            logger.debug(f"File downloaded: {save_path}")
        else:
            error_msg = f"Failed to download file: {response.status_code} - {response.text}"
            logger.error(error_msg)
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
                logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Error making API request: {str(e)}")
            raise

class ApiJiraFieldMappingProvider(JiraFieldMappingProvider):
    """Jira API에서 필드 매핑 데이터를 가져오는 제공자"""
    
    def __init__(self, jira_api_client):
        self.jira_api_client = jira_api_client
        self.field_mappings = {}
        self.initialized = False
    
    def get_field_mapping(self) -> Dict[str, str]:
        if not self.initialized:
            self.refresh()
        return self.field_mappings
    
    def refresh(self) -> None:
        try:
            # Jira API를 통해 필드 정보 가져오기
            response = self.jira_api_client._make_request('GET', '/rest/api/2/field')
            
            # 매핑 구성
            mappings = {}
            for field in response:
                if 'key' in field and 'name' in field:
                    field_id = field['key']
                    # 사람이 읽기 쉬운 형식으로 변환
                    field_name = field['name'].lower().replace(' ', '_')
                    mappings[field_id] = field_name
            
            self.field_mappings = mappings
            self.initialized = True
            logger.info("Field mappings loaded from Jira API")
            
        except Exception as e:
            logger.error(f"Failed to load field mappings from API: {str(e)}")
            # 실패 시 빈 매핑 사용
            self.field_mappings = {}
            self.initialized = True

    def get_field_mapping_file_path(self) -> str:
        """필드 매핑 파일 경로 반환"""
        return os.environ.get(
            'JIRA_FIELD_MAPPING', 
            '/workspace/app/config/jira_field_mapping.json'
        )
    

class FileJiraFieldMappingProvider(JiraFieldMappingProvider):
    """파일에서 필드 매핑 데이터를 로드하는 제공자"""
    
    def __init__(self, file_path=None):
        self.file_path = file_path or os.environ.get(
            'JIRA_FIELD_MAPPING', 
            '/workspace/app/config/jira_field_mapping.json'
        )
        self.field_mappings = {}
        self.initialized = False
    
    def get_field_mappings(self) -> Dict[str, str]:
        if not self.initialized:
            self.refresh()
        return self.field_mappings
    
    def refresh(self) -> None:
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    self.field_mappings = json.load(f)
                logger.info(f"Field mappings loaded from {self.file_path}")
            else:
                logger.warning(f"Mapping file not found: {self.file_path}")
                self.field_mappings = {}
            
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Failed to load field mappings from file: {str(e)}")
            self.field_mappings = {}
            self.initialized = True

class JiraFieldMapperimpl(JiraFieldMapper):
    """Jira 필드 ID를 사람이 읽을 수 있는 이름으로 매핑"""
    
    def __init__(self, mapping_provider: JiraFieldMappingProvider = None):
        self.mapping_provider = mapping_provider
    
    def set_mapping_provider(self, provider: JiraFieldMappingProvider):
        """런타임에 매핑 제공자 변경"""
        self.mapping_provider = provider
    
    def map_field_id_to_name(self, field_id: str) -> str:
        """필드 ID를 이름으로 변환"""
        if not field_id.startswith('customfield_'):
            return field_id
            
        mappings = self.mapping_provider.get_field_mapping()
        return mappings.get(field_id, field_id)
    
    def map_field_name_to_id(self, field_name: str) -> str:
        """이름을 필드 ID로 변환 (역매핑)"""
        mappings = self.mapping_provider.get_field_mapping()
        reverse_mapping = {v: k for k, v in mappings.items()}
        return reverse_mapping.get(field_name, field_name)
    
    def transform_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """응답 데이터의 필드 키를 변환"""
        if 'fields' not in response_data:
            return response_data
            
        transformed = response_data.copy()
        mapped_fields = {}
        
        for field_id, value in response_data['fields'].items():
            if field_id.startswith('customfield_'):
                field_name = self.map_field_id_to_name(field_id)
                mapped_fields[field_name] = value
            else:
                mapped_fields[field_id] = value
                
        transformed['fields'] = mapped_fields
        return transformed
    
    def refresh_mappings(self):
        """매핑 데이터 새로고침"""
        self.mapping_provider.refresh()

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
