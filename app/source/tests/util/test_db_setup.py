import asyncio
from typing import Dict, Any, List, Optional
from app.source.infrastructure.database.connection import get_database_connection

class TestDatabaseSetup:
    """테스트를 위한 데이터베이스 설정 및 관리"""
    
    def __init__(self):
        self.db = get_database_connection()
        
    async def setup_db(self):
        """테스트 데이터베이스 초기화"""
        await self.db.connect()
        
    async def teardown_db(self):
        """테스트 데이터베이스 정리"""
        await self.cleanup_test_data()
        await self.db.disconnect()
    
    async def cleanup_test_data(self):
        """테스트 데이터 삭제"""
        try:
            # 테이블 존재 여부 확인 후 데이터 삭제
            tables = ['employees', 'companies', 'research_projects', 'experts']
            
            for table in tables:
                if await self._table_exists(table):
                    await self.db.execute(f"DELETE FROM {table} WHERE id LIKE 'TEST-%'")
        except Exception as e:
            print(f"Error cleaning up test data: {e}")
    
    async def _table_exists(self, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """
        result = await self.db.fetch_one(query, (table_name,))
        return result[0] if result else False
    
    async def create_test_employees(self, employees: List[Dict[str, Any]]) -> List[str]:
        """테스트용 직원 데이터 생성"""
        employee_ids = []
        
        for employee in employees:
            query = """
                INSERT INTO employees (
                    id, name, email, department, position, jira_account_id
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """
            values = (
                employee.get('id', f"TEST-EMP-{len(employee_ids)+1}"),
                employee.get('name', ''),
                employee.get('email', ''),
                employee.get('department', ''),
                employee.get('position', ''),
                employee.get('jira_account_id', '')
            )
            
            result = await self.db.fetch_one(query, values)
            employee_ids.append(result['id'])
            
        return employee_ids
    
    async def create_test_companies(self, companies: List[Dict[str, Any]]) -> List[str]:
        """테스트용 회사 데이터 생성"""
        company_ids = []
        
        for company in companies:
            query = """
                INSERT INTO companies (
                    id, company_name, biz_id, address
                ) VALUES ($1, $2, $3, $4)
                RETURNING id
            """
            values = (
                company.get('id', f"TEST-COMP-{len(company_ids)+1}"),
                company.get('company_name', ''),
                company.get('biz_id', ''),
                company.get('address', '')
            )
            
            result = await self.db.fetch_one(query, values)
            company_ids.append(result['id'])
            
        return company_ids
    
    async def create_test_research_projects(self, projects: List[Dict[str, Any]]) -> List[str]:
        """테스트용 연구 프로젝트 데이터 생성"""
        project_ids = []
        
        for project in projects:
            query = """
                INSERT INTO research_projects (
                    id, project_code, project_name, project_period, project_manager
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """
            values = (
                project.get('id', f"TEST-PROJ-{len(project_ids)+1}"),
                project.get('project_code', ''),
                project.get('project_name', ''),
                project.get('project_period', ''),
                project.get('project_manager', '')
            )
            
            result = await self.db.fetch_one(query, values)
            project_ids.append(result['id'])
            
        return project_ids 