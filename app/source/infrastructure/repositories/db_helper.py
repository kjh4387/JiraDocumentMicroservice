from typing import Dict, Any, Optional
from app.source.config.di_container import DIContainer
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.infrastructure.persistence.schema_definition import SchemaRegistry, create_company_schema, create_employee_schema, create_research_schema, create_expert_schema, TableSchema
from app.source.infrastructure.repositories.company_repo_v2 import CompanyRepositoryV2
from app.source.infrastructure.repositories.employee_repo_v2 import EmployeeRepositoryV2
from app.source.infrastructure.repositories.research_repo_v2 import ResearchRepositoryV2
from app.source.infrastructure.repositories.expert_repo_v2 import ExpertRepositoryV2
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
from app.source.config.settings import Settings
from app.source.main import load_config

def get_db_connection() -> DatabaseConnection:
    """데이터베이스 연결 가져오기"""
    container = DIContainer(load_config())
    return container.db_connection


def get_company_repo() -> CompanyRepositoryV2:
    """회사 저장소 가져오기"""
    container = DIContainer(load_config())
    return container.company_repo

def get_employee_repo() -> EmployeeRepositoryV2:
    """직원 저장소 가져오기"""
    container = DIContainer(load_config())
    return container.employee_repo

def get_research_repo() -> ResearchRepositoryV2:
    """연구 저장소 가져오기"""
    container = DIContainer(load_config())
    return container.research_repo  

def get_expert_repo() -> ExpertRepositoryV2:
    """전문가 저장소 가져오기"""
    container = DIContainer(load_config())
    return container.expert_repo

def get_schema_registry() -> SchemaRegistry:
    """스키마 레지스트리 가져오기"""
    container = DIContainer(load_config())
    return container.schema_registry

def create_employee_table() -> TableSchema:
    """db에 employee 테이블 생성"""
    sql = get_employee_repo().schema.create_table_sql()
    get_db_connection().execute_query(sql)
    return get_employee_repo().schema

def create_company_table() -> TableSchema:
    """db에 company 테이블 생성"""
    sql = get_company_repo().schema.create_table_sql()
    get_db_connection().execute_query(sql)
    return get_company_repo().schema

def create_research_table() -> TableSchema:
    """db에 research 테이블 생성"""
    sql = get_research_repo().schema.create_table_sql()
    get_db_connection().execute_query(sql)
    return get_research_repo().schema       

def create_expert_table() -> TableSchema:
    """db에 expert 테이블 생성"""
    sql = get_expert_repo().schema.create_table_sql()
    get_db_connection().execute_query(sql)
    return get_expert_repo().schema

def create_all_tables() -> None:
    """모든 테이블 생성"""
    create_employee_table()
    

if __name__ == "__main__":
    create_all_tables()