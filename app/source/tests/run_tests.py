#!/usr/bin/env python3
import os
import sys
import unittest
import time
import importlib.util
import inspect
from collections import defaultdict
import argparse
from typing import List, Optional

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 색상 출력 설정
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # colorama가 없을 경우 대체 구현
    class DummyFore:
        def __getattr__(self, name):
            return ""
    Fore = DummyFore()
    Style = DummyFore()

# 테스트 결과 저장 클래스
class TestResult:
    def __init__(self):
        self.total = 0
        self.success = 0
        self.failure = 0
        self.error = 0
        self.skipped = 0
        self.details = []
        self.duration = 0

def find_test_files(directory):
    """지정된 디렉토리에서 테스트 파일 찾기"""
    test_files = []
    if not os.path.exists(directory):
        print(f"디렉토리가 존재하지 않습니다: {directory}")
        return test_files
        
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files

def extract_test_cases(file_path):
    """파일에서 테스트 케이스 및 메서드 추출"""
    try:
        # 파일 경로에서 모듈 이름 추출
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 모듈 로드
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 테스트 케이스 클래스 찾기
        test_cases = []
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                # 테스트 메서드 찾기
                test_methods = []
                for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if method_name.startswith("test_"):
                        test_methods.append(method_name)
                
                if test_methods:
                    test_cases.append((name, test_methods))
        
        return test_cases
    except Exception as e:
        print(f"{Fore.RED}Error extracting test cases from {file_path}: {str(e)}")
        return []

def discover_tests(start_dir: str, pattern: str = 'test_*.py') -> unittest.TestSuite:
    """지정된 디렉토리에서 테스트를 발견하여 테스트 스위트 반환"""
    loader = unittest.TestLoader()
    return loader.discover(start_dir, pattern=pattern)

def run_tests(test_suite: unittest.TestSuite) -> unittest.TestResult:
    """테스트 스위트를 실행하고 결과 반환"""
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(test_suite)

def print_summary(result: unittest.TestResult, test_type: str, start_time: float, end_time: float):
    """테스트 결과 요약 출력"""
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print(f"{Fore.GREEN}{test_type} 테스트 결과: 성공{Fore.RESET}")
    else:
        print(f"{Fore.RED}{test_type} 테스트 결과: 실패{Fore.RESET}")
        
    print(f"실행 시간:{Fore.RESET} {duration:.2f}초")
    print(f"테스트 수:{Fore.RESET} {result.testsRun}")
    print(f"성공:{Fore.RESET} {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패:{Fore.RESET} {len(result.failures)}")
    print(f"에러:{Fore.RESET} {len(result.errors)}")
    
    if result.failures:
        print(f"\n{Fore.RED}실패한 테스트:{Fore.RESET}")
        for failure in result.failures:
            print(f"- {failure[0]}")
    
    if result.errors:
        print(f"\n{Fore.RED}에러가 발생한 테스트:{Fore.RESET}")
        for error in result.errors:
            print(f"- {error[0]}")
    
    print("=" * 80 + "\n")

def run_unit_tests() -> bool:
    """단위 테스트 실행"""
    print(f"\n{Fore.BLUE}단위 테스트 실행 중...{Fore.RESET}\n")
    
    start_time = time.time()
    test_suite = discover_tests('app/source/tests/unit')
    result = run_tests(test_suite)
    end_time = time.time()
    
    print_summary(result, "단위", start_time, end_time)
    return result.wasSuccessful()

def run_integration_tests() -> bool:
    """통합 테스트 실행"""
    print(f"\n{Fore.BLUE}통합 테스트 실행 중...{Fore.RESET}\n")
    
    start_time = time.time()
    test_suite = discover_tests('app/source/tests/integration')
    result = run_tests(test_suite)
    end_time = time.time()
    
    print_summary(result, "통합", start_time, end_time)
    return result.wasSuccessful()

def run_all_tests() -> bool:
    """모든 테스트 실행"""
    print(f"\n{Fore.BLUE}모든 테스트 실행 중...{Fore.RESET}\n")
    
    start_time = time.time()
    test_suite = unittest.TestSuite()
    
    # 단위 테스트 추가
    unit_tests = discover_tests('app/source/tests/unit')
    test_suite.addTest(unit_tests)
    
    # 통합 테스트 추가
    integration_tests = discover_tests('app/source/tests/integration')
    test_suite.addTest(integration_tests)
    
    result = run_tests(test_suite)
    end_time = time.time()
    
    print_summary(result, "전체", start_time, end_time)
    return result.wasSuccessful()

def run_specific_test(test_path: str) -> bool:
    """특정 테스트 파일 실행"""
    if not test_path.endswith('.py'):
        test_path += '.py'
    
    if not os.path.isfile(test_path):
        # tests 디렉토리 내에서 찾기 시도
        alt_path = os.path.join('app/source/tests', test_path)
        if os.path.isfile(alt_path):
            test_path = alt_path
        else:
            print(f"{Fore.RED}테스트 파일을 찾을 수 없습니다: {test_path}{Fore.RESET}")
            return False
    
    print(f"\n{Fore.BLUE}특정 테스트 파일 실행 중: {test_path}...{Fore.RESET}\n")
    
    dir_path = os.path.dirname(test_path)
    file_name = os.path.basename(test_path)
    
    start_time = time.time()
    test_suite = discover_tests(dir_path, pattern=file_name)
    result = run_tests(test_suite)
    end_time = time.time()
    
    print_summary(result, f"파일 ({file_name})", start_time, end_time)
    return result.wasSuccessful()

def run_repository_tests() -> bool:
    """Repository 관련 테스트 실행"""
    print(f"\n{Fore.BLUE}Repository 테스트 실행 중...{Fore.RESET}\n")
    
    test_suite = unittest.TestSuite()
    
    # 단위 테스트에서 Repository 테스트 추가
    for file in os.listdir('app/source/tests/unit'):
        if file.startswith('test_') and file.endswith('_repository.py'):
            unit_path = os.path.join('app/source/tests/unit', file)
            unit_tests = discover_tests(os.path.dirname(unit_path), pattern=os.path.basename(unit_path))
            test_suite.addTest(unit_tests)
    
    # 통합 테스트에서 Repository 테스트 추가
    for file in os.listdir('app/source/tests/integration'):
        if file.startswith('test_') and ('repository' in file.lower()) and file.endswith('.py'):
            int_path = os.path.join('app/source/tests/integration', file)
            int_tests = discover_tests(os.path.dirname(int_path), pattern=os.path.basename(int_path))
            test_suite.addTest(int_tests)
    
    start_time = time.time()
    result = run_tests(test_suite)
    end_time = time.time()
    
    print_summary(result, "Repository", start_time, end_time)
    return result.wasSuccessful()

def run_service_tests() -> bool:
    """Service 관련 테스트 실행"""
    print(f"\n{Fore.BLUE}Service 테스트 실행 중...{Fore.RESET}\n")
    
    test_suite = unittest.TestSuite()
    
    # 단위 테스트에서 Service 테스트 추가
    for file in os.listdir('app/source/tests/unit'):
        if file.startswith('test_') and ('service' in file.lower()) and file.endswith('.py'):
            unit_path = os.path.join('app/source/tests/unit', file)
            unit_tests = discover_tests(os.path.dirname(unit_path), pattern=os.path.basename(unit_path))
            test_suite.addTest(unit_tests)
    
    # 통합 테스트에서 Service 테스트 추가
    for file in os.listdir('app/source/tests/integration'):
        if file.startswith('test_') and ('service' in file.lower()) and file.endswith('.py'):
            int_path = os.path.join('app/source/tests/integration', file)
            int_tests = discover_tests(os.path.dirname(int_path), pattern=os.path.basename(int_path))
            test_suite.addTest(int_tests)
    
    start_time = time.time()
    result = run_tests(test_suite)
    end_time = time.time()
    
    print_summary(result, "Service", start_time, end_time)
    return result.wasSuccessful()

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='테스트 실행기')
    
    # 테스트 유형 선택 인자
    parser.add_argument('-u', '--unit', action='store_true', help='단위 테스트만 실행')
    parser.add_argument('-i', '--integration', action='store_true', help='통합 테스트만 실행')
    parser.add_argument('-a', '--all', action='store_true', help='모든 테스트 실행')
    parser.add_argument('-r', '--repository', action='store_true', help='Repository 관련 테스트 실행')
    parser.add_argument('-s', '--service', action='store_true', help='Service 관련 테스트 실행')
    parser.add_argument('-f', '--file', type=str, help='특정 테스트 파일 실행')
    
    args = parser.parse_args()
    
    success = True
    
    if args.unit:
        success = run_unit_tests() and success
    elif args.integration:
        success = run_integration_tests() and success
    elif args.repository:
        success = run_repository_tests() and success
    elif args.service:
        success = run_service_tests() and success
    elif args.file:
        success = run_specific_test(args.file) and success
    elif args.all:
        success = run_all_tests() and success
    else:
        # 기본적으로 모든 테스트 실행
        success = run_all_tests() and success
    
    # 성공/실패 상태 코드 반환
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 