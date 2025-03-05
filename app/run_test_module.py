#!/usr/bin/env python
import sys
import os
import unittest

# 앱 디렉토리를 Python 경로에 추가
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

def run_test_module(module_path):
    """지정된 테스트 모듈 실행"""
    try:
        # 상대 경로를 임포트 경로로 변환 (예: tests/core/test_schema_registry -> tests.core.test_schema_registry)
        module_name = module_path.replace('/', '.').rstrip('.py')
        
        # 모듈 로드 및 실행
        suite = unittest.TestLoader().loadTestsFromName(module_name)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return 0 if result.wasSuccessful() else 1
    
    except Exception as e:
        print(f"테스트 모듈 실행 오류: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python run_test_module.py <테스트_모듈_경로>")
        print("예: python run_test_module.py tests.core.test_schema_registry")
        sys.exit(1)
    
    module_path = sys.argv[1]
    sys.exit(run_test_module(module_path)) 