import unittest
from unittest.mock import patch, MagicMock
from app.source.infrastructure.integrations.jira_client import JiraClient

class TestJiraClient(unittest.TestCase):
    
    @patch.dict('os.environ', {
        'JIRA_BASE_URL': 'https://msimul.atlassian.net',
        'JIRA_USERNAME': 'test@example.com',
        'JIRA_API_TOKEN': 'test-token'
    })
    def test_init_from_env_vars(self):
        """환경변수에서 설정 로드 테스트"""
        client = JiraClient()
        self.assertEqual(client.jira_base_url, 'https://msimul.atlassian.net')
    
    @patch('requests.get')
    def test_get_issue(self, mock_get):
        """이슈 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'fields': {'summary': 'Test Issue'}}
        mock_get.return_value = mock_response
        
        # 테스트 실행
        client = JiraClient('https://test.atlassian.net', 'user', 'token')
        result = client.get_issue('TEST-123')
        
        # 검증
        self.assertEqual(result['fields']['summary'], 'Test Issue')
        mock_get.assert_called_once()
    
    # 다른 메서드에 대한 테스트...
