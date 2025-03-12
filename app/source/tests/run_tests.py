#!/usr/bin/env python3
import os
import sys
import unittest
import time
import importlib.util
import inspect
from collections import defaultdict

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

def run_tests(test_path, test_type="unit"):
    """테스트 실행 및 결과 반환"""
    # 테스트 로더 생성
    loader = unittest.TestLoader()
    
    # 테스트 스위트 생성
    if os.path.isfile(test_path):
        # 파일인 경우 해당 파일만 로드
        suite = loader.discover(os.path.dirname(test_path), pattern=os.path.basename(test_path))
    else:
        # 디렉토리인 경우 모든 테스트 파일 로드
        suite = loader.discover(test_path, pattern="test_*.py")
    
    # 테스트 실행 결과 저장 객체
    result = TestResult()
    
    # 결과 저장용 TextTestRunner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # 시간 측정 시작
    start_time = time.time()
    
    # 테스트 실행
    test_result = runner.run(suite)
    
    # 시간 측정 종료
    end_time = time.time()
    
    # 결과 저장
    result.total = test_result.testsRun
    result.success = result.total - len(test_result.failures) - len(test_result.errors) - len(test_result.skipped)
    result.failure = len(test_result.failures)
    result.error = len(test_result.errors)
    result.skipped = len(test_result.skipped)
    result.duration = end_time - start_time
    
    # 상세 결과 저장
    for test, error in test_result.failures:
        result.details.append((str(test), "FAIL", str(error)[:100] + "..." if len(str(error)) > 100 else str(error)))
    
    for test, error in test_result.errors:
        result.details.append((str(test), "ERROR", str(error)[:100] + "..." if len(str(error)) > 100 else str(error)))
    
    for test, reason in test_result.skipped:
        result.details.append((str(test), "SKIPPED", reason))
    
    return result

def print_test_structure(unit_files, integration_files):
    """테스트 구조 출력"""
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}테스트 구조")
    print(f"{Fore.CYAN}{'=' * 80}")
    
    # 단위 테스트 구조 출력
    print(f"\n{Fore.YELLOW}Unit Tests:")
    for file_path in unit_files:
        rel_path = os.path.relpath(file_path, start=os.path.join(os.getcwd(), "app", "source"))
        print(f"{Fore.GREEN}{rel_path}")
        
        test_cases = extract_test_cases(file_path)
        for case_name, methods in test_cases:
            print(f"{Fore.BLUE}  └─ {case_name}")
            for method in methods:
                print(f"{Fore.WHITE}     └─ {method}")
    
    # 통합 테스트 구조 출력
    print(f"\n{Fore.YELLOW}Integration Tests:")
    for file_path in integration_files:
        rel_path = os.path.relpath(file_path, start=os.path.join(os.getcwd(), "app", "source"))
        print(f"{Fore.GREEN}{rel_path}")
        
        test_cases = extract_test_cases(file_path)
        for case_name, methods in test_cases:
            print(f"{Fore.BLUE}  └─ {case_name}")
            for method in methods:
                print(f"{Fore.WHITE}     └─ {method}")

def print_results(unit_result, integration_result):
    """테스트 결과 출력"""
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}테스트 결과 요약")
    print(f"{Fore.CYAN}{'=' * 80}")
    
    # 단위 테스트 결과
    print(f"\n{Fore.YELLOW}Unit Tests:")
    print(f"{Fore.WHITE}Total: {unit_result.total}, "
          f"Success: {Fore.GREEN}{unit_result.success}{Fore.WHITE}, "
          f"Failure: {Fore.RED}{unit_result.failure}{Fore.WHITE}, "
          f"Error: {Fore.RED}{unit_result.error}{Fore.WHITE}, "
          f"Skipped: {Fore.YELLOW}{unit_result.skipped}")
    print(f"Duration: {unit_result.duration:.2f} seconds")
    
    # 통합 테스트 결과
    print(f"\n{Fore.YELLOW}Integration Tests:")
    print(f"{Fore.WHITE}Total: {integration_result.total}, "
          f"Success: {Fore.GREEN}{integration_result.success}{Fore.WHITE}, "
          f"Failure: {Fore.RED}{integration_result.failure}{Fore.WHITE}, "
          f"Error: {Fore.RED}{integration_result.error}{Fore.WHITE}, "
          f"Skipped: {Fore.YELLOW}{integration_result.skipped}")
    print(f"Duration: {integration_result.duration:.2f} seconds")
    
    # 총 결과
    total = unit_result.total + integration_result.total
    success = unit_result.success + integration_result.success
    failure = unit_result.failure + integration_result.failure
    error = unit_result.error + integration_result.error
    skipped = unit_result.skipped + integration_result.skipped
    duration = unit_result.duration + integration_result.duration
    
    print(f"\n{Fore.YELLOW}Total Summary:")
    print(f"{Fore.WHITE}Total: {total}, "
          f"Success: {Fore.GREEN}{success}{Fore.WHITE}, "
          f"Failure: {Fore.RED}{failure}{Fore.WHITE}, "
          f"Error: {Fore.RED}{error}{Fore.WHITE}, "
          f"Skipped: {Fore.YELLOW}{skipped}")
    print(f"Total Duration: {duration:.2f} seconds")
    
    # 실패 및 에러 상세 정보
    if unit_result.failure > 0 or unit_result.error > 0 or integration_result.failure > 0 or integration_result.error > 0:
        print(f"\n{Fore.RED}{'=' * 80}")
        print(f"{Fore.RED}실패 및 에러 상세 정보")
        print(f"{Fore.RED}{'=' * 80}")
        
        for test, status, message in unit_result.details + integration_result.details:
            if status in ["FAIL", "ERROR"]:
                color = Fore.RED
            else:
                color = Fore.YELLOW
                
            print(f"\n{color}{status}: {test}")
            print(f"{Fore.WHITE}{message}")

def main():
    """메인 함수"""
    # 현재 작업 디렉토리 확인
    cwd = os.getcwd()
    
    # 테스트 디렉토리 경로 설정
    unit_test_dir = os.path.join(cwd, "app", "source", "tests", "unit")
    integration_test_dir = os.path.join(cwd, "app", "source", "tests", "integration")
    
    # 테스트 파일 찾기
    unit_files = find_test_files(unit_test_dir)
    integration_files = find_test_files(integration_test_dir)
    
    # 테스트 구조 출력
    print_test_structure(unit_files, integration_files)
    
    # 테스트 실행
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}테스트 실행 중...")
    print(f"{Fore.CYAN}{'=' * 80}")
    
    # 단위 테스트 실행
    print(f"\n{Fore.YELLOW}Running Unit Tests...")
    unit_result = run_tests(unit_test_dir, "unit")
    
    # 통합 테스트 실행
    print(f"\n{Fore.YELLOW}Running Integration Tests...")
    integration_result = run_tests(integration_test_dir, "integration")
    
    # 결과 출력
    print_results(unit_result, integration_result)

if __name__ == "__main__":
    main() 