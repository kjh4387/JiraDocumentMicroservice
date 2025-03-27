from typing import Dict, Any, List, Optional
import logging
from app.source.core.exceptions import MappingError
from app.source.infrastructure.mapping.markdown_parser import MarkdownTableParser
import json

class JiraDocumentMapper:
    """Jira 응답의 특정 필드들을 전처리하는 매퍼"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Args:
            logger: 로거 인스턴스. 기본값은 None
        """
        self.logger = logger or logging.getLogger(__name__)
        self.markdown_parser = MarkdownTableParser()
        self.logger.info("JiraDocumentMapper initialized")
    
    def preprocess_fields(self, jira_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Jira 응답에서 특정 필드들을 전처리
        
        Args:
            jira_response: Jira API 응답 데이터
            
        Returns:
            전처리된 필드들이 포함된 데이터
            
        Raises:
            MappingError: 전처리 중 오류 발생 시
        """
        try:
            self.logger.debug("Preprocessing Jira response fields")
            
            # 원본 데이터 유지하면서 전처리된 필드만 추가
            processed_data = jira_response.copy()
            fields = processed_data.get("fields", {})
            
            
            # Markdown 테이블 필드들 전처리
            if "internal_participants_table" in fields:
                fields["internal_participants"] = self._preprocess_markdown_table(fields["internal_participants_table"])
            
            if "external_participants_table" in fields:
                fields["external_participants"] = self._preprocess_markdown_table(fields["external_participants_table"])
            
            if "items_table" in fields:
                fields["items"] = self._preprocess_markdown_table(fields["items_table"])
            
            processed_data["fields"] = fields
            self.logger.info("Successfully preprocessed fields")
            return processed_data
            
        except Exception as e:
            self.logger.error("Error preprocessing fields: %s", str(e), exc_info=True)
            raise MappingError(f"필드 전처리 중 오류 발생: {str(e)}")
    
    def _preprocess_markdown_table(self, table_content: str) -> List[Dict[str, Any]]:
        """Markdown 테이블을 파싱하여 구조화된 데이터로 변환
        
        Args:
            table_content: Markdown 형식의 테이블 문자열
            
        Returns:
            파싱된 테이블 데이터 리스트
        """
        try:
            if not table_content:
                return []
                
            parsed_data = self.markdown_parser.parse_table(table_content)
            self.logger.debug("Parsed markdown table: %s", parsed_data)
            return parsed_data
            
        except Exception as e:
            self.logger.error("Error parsing markdown table: %s", str(e))
            return []
    
if __name__ == "__main__":
    from app.source.infrastructure.integrations.jira_client import JiraClient
    import os

    from app.source.infrastructure.mapping.jira_field_mapper import ApiJiraFieldMappingProvider, JiraFieldMapperimpl
    JIRA_URL = os.getenv("JIRA_BASE_URL")
    JIRA_USER = os.getenv("JIRA_USERNAME")
    JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    mapping_provider = ApiJiraFieldMappingProvider(JiraClient(JIRA_URL, JIRA_USER, JIRA_TOKEN))
    field_mapper = JiraFieldMapperimpl(mapping_provider)
    
    jira_client = JiraClient(JIRA_URL, JIRA_USER, JIRA_TOKEN, field_mapper=field_mapper)
    mapper = JiraDocumentMapper()
    
    # 테스트
    issue_data = jira_client.get_issue('ACCO-74')
    processed_data = mapper.preprocess_fields(issue_data)
    print("Preprocessed data:", json.dumps(processed_data, ensure_ascii=False, indent=2))
    