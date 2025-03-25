import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional

from app.source.config.di_container import DIContainer
from app.source.tests.util.test_fixtures import TestFixtures, MockDatabaseConnection, get_test_config, TestDatabaseHelper


class BaseUnitTest(unittest.TestCase):
    """단위 테스트를 위한 기본 클래스
    
    모든 외부 의존성(DB 등)은 모킹하여 진정한 단위 테스트를 가능하게 함
    """
    
    def setUp(self):
        """테스트 설정"""
        # 모의 객체 설정
        self.db_mock = MockDatabaseConnection()
        
        # 픽스처 사용 준비
        self.fixtures = TestFixtures()
        
        # 패치 적용
        self.patches = []
        self._apply_patches()
    
    def tearDown(self):
        """테스트 정리"""
        # 패치 제거
        for p in self.patches:
            p.stop()
    
    def _apply_patches(self):
        """필요한 패치 적용"""
        # 데이터베이스 연결을 모의 객체로 패치
        db_patch = patch('app.source.infrastructure.persistence.db_connection.DatabaseConnection', return_value=self.db_mock)
        self.patches.append(db_patch)
        db_patch.start()
        
        # 필요에 따라 추가 패치 적용 가능
    
    def set_db_find_result(self, entity_data: Dict[str, Any] = None):
        """조회 결과 설정"""
        # 기본 빈 결과
        result = []
        
        # 엔티티 데이터가 제공되면 조회 결과로 설정
        if entity_data:
            result = [entity_data]
        
        # SELECT 쿼리에 대한 기본 결과 설정
        self.db_mock.set_default_result(result)
    
    def assert_query_called_with(self, query_substring: str, params=None):
        """특정 쿼리가 호출되었는지 확인"""
        for query_call in self.db_mock.executed_queries:
            if query_substring in query_call["query"]:
                if params is None or params == query_call["params"]:
                    return True
        
        self.fail(f"Query containing '{query_substring}' was not called with params={params}")


class BaseIntegrationTest(unittest.TestCase):
    """통합 테스트를 위한 기본 클래스
    
    실제 DB와 상호작용하여 Repository 계층의 통합 테스트를 수행
    """
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # 테스트 설정 로드
        cls.config = get_test_config()
        
        # DB 헬퍼 초기화
        cls.db_helper = TestDatabaseHelper(cls.config)
        
        # 테스트 DB 설정
        cls.db_helper.setup_test_db()
        
        # DI 컨테이너 초기화
        cls.container = DIContainer(cls.config)
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        # 테스트 데이터 정리
        cls.db_helper.cleanup_test_db()
    
    def setUp(self):
        """테스트 설정"""
        # 픽스처 준비
        self.fixtures = TestFixtures()
        
        # 각 테스트 메서드 시작 시 필요한 작업
    
    def tearDown(self):
        """테스트 정리"""
        # 개별 테스트에서 생성한 데이터 정리는 tearDownClass에서 수행
        pass 