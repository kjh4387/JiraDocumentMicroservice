from setuptools import setup, find_packages

setup(
    name="my_package",           # 패키지 이름
    version="0.1.0",
    packages=find_packages(where="source"),  # source 폴더 아래 패키지 검색
    package_dir={"": "source"},  # 실제 소스가 들어있는 폴더 지정
    install_requires=[],         # 의존성이 있다면 여기에 기재
    python_requires=">=3.7"      # 지원 파이썬 버전
)
