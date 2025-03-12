import unittest
from unittest.mock import MagicMock, patch
from app.source.core.domain import Research
from app.source.infrastructure.repositories.research_repo import ResearchRepository
from app.source.core.exceptions import DatabaseError

class TestResearchRepository(unittest.TestCase):
    
    def setUp(self):
        # 데이터베이스 연결 모의 객체 생성
        self.db_connection = MagicMock()
        
        # 테스트 대상 저장소 생성
        self.repo = ResearchRepository(self.db_connection)
        
        # 테스트용 연구 과제 데이터
        self.test_research = Research(
            id="PROJ-001",
            project_name="AI 기반 문서 자동화 연구",
            project_code="AI-2023-001",  # project_number 대신 project_code 사용
            project_period="2023-01-01 ~ 2023-12-31",
            project_manager="김연구",
            project_manager_phone="010-9876-5432"
        )
    
    def test_find_by_id(self):
        """ID로 연구 과제 조회 테스트"""
        # Mock 설정
        self.db_connection.execute_query.return_value = [{
            "id": "PROJ-001",
            "project_name": "AI 기반 문서 자동화 연구",
            "project_code": "AI-2023-001",  # project_number 대신 project_code 사용
            "project_period": "2023-01-01 ~ 2023-12-31",
            "project_manager": "김연구",
            "project_manager_phone": "010-9876-5432"
        }]
        
        # 메서드 호출
        result = self.repo.find_by_id("PROJ-001")
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "PROJ-001")
        self.assertEqual(result.project_code, "AI-2023-001")  # project_number 대신 project_code 검증
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM research_projects WHERE id = %s", ("PROJ-001",)
        )
    
    def test_find_by_project_code(self):
        """프로젝트 코드로 연구 과제 조회 테스트 (새로 추가)"""
        # Mock 설정
        self.db_connection.execute_query.return_value = [{
            "id": "PROJ-001",
            "project_name": "AI 기반 문서 자동화 연구",
            "project_code": "AI-2023-001",
            "project_period": "2023-01-01 ~ 2023-12-31",
            "project_manager": "김연구",
            "project_manager_phone": "010-9876-5432"
        }]
        
        # 메서드 호출
        result = self.repo.find_by_project_code("AI-2023-001")
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "PROJ-001")
        self.assertEqual(result.project_code, "AI-2023-001")
        self.db_connection.execute_query.assert_called_once_with(
            "SELECT * FROM research_projects WHERE project_code = %s", ("AI-2023-001",)
        )
    
    def test_save(self):
        """연구 과제 정보 저장 테스트"""
        # Mock 설정 - 과제가 존재하지 않는 경우
        self.db_connection.execute_query.side_effect = [
            [],  # find_by_id 호출 결과 (존재하지 않음)
            []   # INSERT 쿼리 결과
        ]
        
        # 저장 메서드 호출
        result = self.repo.save(self.test_research)
        
        # 검증
        self.assertEqual(result.id, self.test_research.id)
        self.assertEqual(result.project_code, self.test_research.project_code)
        
        # 두 번째 호출은 INSERT 쿼리
        _, args, _ = self.db_connection.execute_query.mock_calls[1]
        self.assertIn("INSERT INTO", args[0])
        self.assertIn("research", args[0])  # research_projects 또는 researches 테이블 이름에 모두 적용 가능
    
    def test_find_by_project_code_not_found(self):
        """존재하지 않는 프로젝트 코드로 조회 테스트 (새로 추가)"""
        # Mock 설정 - 결과 없음
        self.db_connection.execute_query.return_value = []
        
        # 조회 메서드 호출
        result = self.repo.find_by_project_code("NOT-EXIST-CODE")
        
        # 검증
        self.assertIsNone(result)
        self.db_connection.execute_query.assert_called_once()

if __name__ == '__main__':
    unittest.main() 