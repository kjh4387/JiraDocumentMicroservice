from typing import Dict, Any, List, Optional
from datetime import datetime
from markupsafe import Markup
from app.source.core.exceptions import MappingError
from app.source.infrastructure.mapping.markdown_parser import MarkdownTableParser
import logging
from app.source.core.interfaces import JiraFieldMapper
import re

logger = logging.getLogger(__name__)

class JiraDocumentMapper:
    """Jira 응답을 document_service가 처리할 수 있는 형태로 변환하는 매퍼"""
    
    def __init__(self):
        self.markdown_parser = MarkdownTableParser()
    
    def map_to_document_data(self, jira_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Jira 응답을 document_service에서 사용할 수 있는 dictionary 형태로 변환
        
        """
        try:
            fields = jira_response.get('fields', {})
            
            return {
                'document_type': self._extract_document_type(fields),
                'metadata': self._extract_metadata(jira_response),
                'meeting_info': self._extract_meeting_info(fields),
                'participants': self._extract_participants(fields),
                'project_info': self._extract_project_info(fields),
                'additional_info': self._extract_additional_info(fields)
            }
        except Exception as e:
            issue_key = jira_response.get('key', 'unknown')
            logger.error(f"Failed to map Jira response for issue {issue_key}: {str(e)}")
            raise MappingError(f"Failed to map Jira response: {str(e)}")
    
    def _extract_document_type(self, fields: Dict[str, Any]) -> str:
        """문서 타입 추출"""
        issue_type = fields.get('issuetype', {}).get('name', '')
        document_type_mapping = {
            '견적서': 'estimate',
            '거래명세서': 'trading_statement',
            '회의록': 'meeting_minutes',
            '회의비사용신청서': 'meeting_expense',
            '출장신청서': 'travel_application',
            '출장정산신청서': 'travel_expense',
            '전문가활용계획서': 'expert_util_plan',
            '전문가자문확인서': 'expert_consult_confirm',
            '지출결의서': 'expenditure',
            '구매의뢰서': 'purchase_order'
        }
        return document_type_mapping.get(issue_type, issue_type)
    
    def _extract_metadata(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """메타데이터 추출"""
        return {
            'issue_key': response.get('key'),
            'created_date': self._format_date(response.get('fields', {}).get('created')),
            'updated_date': self._format_date(response.get('fields', {}).get('updated')),
            'status': response.get('fields', {}).get('status', {}).get('name')
        }
    
    def _extract_participants(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """참석자 정보 추출 및 구조화"""
        participants = {
            'internal': self._extract_internal_participants(fields),
            'external': self._extract_external_participants(fields)
        }
        return participants
    
    def _extract_internal_participants(self, fields: Dict[str, Any]) -> List[Dict[str, str]]:
        """내부 참석자 정보 추출"""
        internal_participants = fields.get('회의_참석자(내부_인원)', [])
        
        logger.debug(
            f"Internal participants data structure: {internal_participants}, type: {type(internal_participants)}"
        )
        
        if not internal_participants:
            return []
        
        result = []
        
        for participant in internal_participants:
            logger.debug(f"Processing participant: {participant}, type: {type(participant)}")
            
            # accountId를 기본 식별자로 사용
            if participant.get('accountId'):
                participant_info = {
                    'account_id': participant['accountId'],
                    'display_name': participant.get('displayName', '')
                }
                
                
                result.append(participant_info)
        
        logger.debug(f"Extracted participants: {result}")
        return result
    
    def _extract_external_participants(self, fields: Dict[str, Any]) -> List[Dict[str, str]]:
        """외부 참석자 정보 추출"""
        if '회의_참석자(외부_인원)' not in fields:
            return []
            
        markdown_table = fields['회의_참석자(외부_인원)']
        if not markdown_table:
            return []
            
        participants = self.markdown_parser.parse_table(markdown_table)
        return [
            {
                'name': participant.get('성명', ''),
                'affiliation': participant.get('소속', ''),
                'position': participant.get('직위', '')
            }
            for participant in participants
        ]
    
    def _extract_meeting_info(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """회의 정보 추출"""
        return {
            'meeting_date': self._format_date(fields.get('회의일자')),
            'meeting_place': fields.get('회의_장소'),
            'meeting_agenda': fields.get('회의목적(주제)'),
            'meeting_summary': fields.get('회의록_내용')
        }
    
    def _format_date(self, date_str: Optional[str]) -> str:
        """날짜 문자열 포맷팅"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_items(self, fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """품목 정보 추출 (마크다운 테이블 파싱)"""
        items_table = fields.get('견적서_내역', '')
        items = self.markdown_parser.parse_table(items_table)
        
        processed = []
        for item in items:
            if any(item.values()):  # 빈 행 제외
                processed.append({
                    'name': item.get('품목', ''),
                    'quantity': self._parse_number(item.get('수량', '0')),
                    'unit_price': self._parse_number(item.get('단가', '0')),
                })
        
        return processed
    
    def _parse_number(self, value: str) -> float:
        """문자열을 숫자로 변환"""
        try:
            return float(value.replace(',', ''))
        except (ValueError, AttributeError):
            return 0.0
    
    def _extract_project_info(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """프로젝트 정보 추출"""
        return {
            'project_id': fields.get('project', {}).get('id'),
            'project_name': fields.get('project', {}).get('name'),
            'project_code': self._extract_project_code(fields.get('연구과제_선택', {}))
        }
    
    def _extract_project_code(self, project_info: Dict[str, Any]) -> str:
        """과제 코드 추출"""
        if not project_info:
            return ''
        
        value = project_info.get('value', '')
        # "수출지향형(RS-2023-00217016)" 형태에서 코드만 추출
        match = re.search(r'\((.*?)\)', value)
        return match.group(1) if match else value
    
    def _extract_additional_info(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """추가 정보 추출"""
        return {
            'meeting_summary': fields.get('회의록_내용'),
            'project_code': self._extract_project_code(fields.get('연구과제_선택', {}))
        }
    
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
    
    print(mapper.map_to_document_data(jira_client.get_issue('ACCO-74')))
    