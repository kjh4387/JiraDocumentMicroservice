#!/usr/bin/env python
import sys
import os

# 앱 디렉토리를 Python 경로에 추가


# 테스트 실행기 임포트 및 실행
from app.tests.run_tests import run_tests

if __name__ == "__main__":
    sys.exit(run_tests()) 