from setuptools import setup, find_packages

setup(
    name="app",
    version="0.1.0",
    packages=find_packages(where="source"),
    package_dir={"": "source"},
    install_requires=[
        "pytest>=7.4.0",
        "markupsafe>=2.1.0",
        "python-dateutil>=2.8.2",
        "requests>=2.31.0",
        "jinja2>=3.1.2",
        "weasyprint>=60.1",
        "jsonschema>=4.20.0",
        "python-dotenv>=1.0.0"
    ],
    python_requires=">=3.7",      # 지원 파이썬 버전
    package_data={
        "app": ["**/*.py", "**/*.json", "**/*.html"],
        "app.core": ["**/*.py"],
        "app.infrastructure": ["**/*.py"],
        "app.application": ["**/*.py"],
        "app.config": ["**/*.py", "**/*.json"],
        "app.rendering": ["**/*.py", "**/*.html"],
        "app.validation": ["**/*.py", "**/*.json"]
    }
)
