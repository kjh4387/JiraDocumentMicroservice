from typing import Dict, Any, List, Optional
from app.source.core.interfaces import Repository
from app.source.core.domain import Employee
from app.source.core.exceptions import EntityNotFoundError, DatabaseError
from app.source.infrastructure.persistence.db_connection import DatabaseConnection
import logging


class EmployeeRepository(Repository[Employee]):
    """직원 정보 저장소"""
    
    def __init__(self, db_connection: DatabaseConnection, logger: logging.Logger = None):
        """
        Args:
            db_connection: 데이터베이스 연결
            logger: 로거 인스턴스
        """
        self.db = db_connection
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("EmployeeRepository initialized")
    
    def find_by_id(self, id: str) -> Optional[Employee]:
        """ID로 직원 조회"""
        self.logger.debug("Finding employee by ID", id=id)
        query = "SELECT * FROM employees WHERE id = %s"
        
        try:
            result = self.db.execute_query(query, (id,))
            
            if not result:
                self.Logger.warning("Employee not found", id=id)
                return None
            
            employee = Employee(**result[0])
            self.logger.debug("Employee found", id=id, name=employee.name)
            return employee
        except Exception as e:
            self.logger.error("Database error while finding employee", id=id, error=str(e))
            raise DatabaseError(f"Failed to find employee with ID {id}: {str(e)}")
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Employee]:
        """조건에 맞는 직원 목록 조회"""
        self.logger.debug("Finding employees by criteria", criteria=criteria)
        conditions = []
        params = []
        
        for key, value in criteria.items():
            conditions.append(f"{key} = %s")
            params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM employees WHERE {where_clause}"
        
        try:
            results = self.db.execute_query(query, tuple(params))
            employees = [Employee(**row) for row in results]
            self.logger.debug("Employees found", count=len(employees))
            return employees
        except Exception as e:
            self.logger.error("Database error while finding employees by criteria", criteria=criteria, error=str(e))
            raise DatabaseError(f"Failed to find employees by criteria: {str(e)}")
    
    def find_by_department(self, department: str) -> List[Employee]:
        """부서로 직원 목록 조회"""
        self.logger.debug("Finding employees by department", department=department)
        query = "SELECT * FROM employees WHERE department = %s"
        
        try:
            results = self.db.execute_query(query, (department,))
            employees = [Employee(**row) for row in results]
            self.logger.debug("Employees found", count=len(employees), department=department)
            return employees
        except Exception as e:
            self.logger.error("Database error while finding employees by department", department=department, error=str(e))
            raise DatabaseError(f"Failed to find employees by department {department}: {str(e)}")
    
    def find_by_email(self, email: str) -> Optional[Employee]:
        """이메일로 직원 조회"""
        self.logger.debug("Finding employee by email", email=email)
        query = "SELECT * FROM employees WHERE email = %s"
        
        try:
            result = self.db.execute_query(query, (email,))
            
            if not result:
                self.logger.warning("Employee not found", email=email)
                return None
            
            employee = Employee(**result[0])
            self.logger.debug("Employee found", id=employee.id, email=employee.email)
            return employee
        except Exception as e:
            self.logger.error("Database error while finding employee by email", email=email, error=str(e))
            raise DatabaseError(f"Failed to find employee with email {email}: {str(e)}")
        
    def find_by_jira_account_id(self, account_id: str) -> Optional[Employee]:
        """Jira account ID로 직원 조회"""
        self.logger.debug("Finding employee by Jira account ID", jira_account_id=account_id)
        query = "SELECT * FROM employees WHERE jira_account_id = %s"
        
        try:
            result = self.db.execute_query(query, (account_id,))
            
            if not result:
                self.logger.warning("Employee not found", jira_account_id=account_id)
                return None 
            
            employee = Employee(**result[0])
            self.logger.debug("Employee found", id=employee.id, jira_account_id=account_id)
            return employee
        except Exception as e:
            self.logger.error("Database error while finding employee by Jira account ID", jira_account_id=account_id, error=str(e))
            raise DatabaseError(f"Failed to find employee with Jira account ID {account_id}: {str(e)}")
        

    def save(self, employee: Employee) -> Employee:
        """직원 정보 저장"""
        self.logger.debug("Saving employee", id=employee.id, name=employee.name)
        
        # 기존 직원 확인
        existing = self.find_by_id(employee.id)
        
        if existing:
            # 업데이트
            query = """
                UPDATE employees 
                SET name = %s, department = %s, position = %s, email = %s,
                    phone = %s, signature = %s, stamp = %s, bank_name = %s, account_number = %s, birth_date = %s, address = %s, fax = %s
                WHERE id = %s
            """
            params = (
                employee.name, employee.department, employee.position, employee.email,
                employee.phone, employee.signature, employee.stamp, employee.bank_name, employee.account_number, employee.birth_date, employee.address, employee.fax, employee.id
            )
            try:
                self.db.execute_query(query, params)
                self.logger.info("Employee updated", id=employee.id, name=employee.name)
            except Exception as e:
                self.logger.error("Database error while updating employee", id=employee.id, error=str(e))
                raise DatabaseError(f"Failed to update employee {employee.id}: {str(e)}")
        else:
            # 삽입
            query = """
                INSERT INTO employees 
                (id, name, email, department, position, phone, signature, stamp, bank_name, account_number, birth_date, address, fax)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                employee.id, employee.name, employee.email, employee.department, employee.position,
                employee.phone, employee.signature, employee.stamp, employee.bank_name, employee.account_number, employee.birth_date, employee.address, employee.fax
            )
            try:
                self.db.execute_query(query, params)
                self.logger.info("Employee created", id=employee.id, name=employee.name)
            except Exception as e:
                self.logger.error("Database error while creating employee", id=employee.id, error=str(e))
                raise DatabaseError(f"Failed to create employee {employee.id}: {str(e)}")
        
        return employee
    
    def delete(self, id: str) -> bool:
        """직원 정보 삭제"""
        self.logger.debug("Deleting employee", id=id)
        
        # 기존 직원 확인
        existing = self.find_by_id(id)
        
        if not existing:
            self.logger.warning("Cannot delete: Employee not found", id=id)
            return False
        
        query = "DELETE FROM employees WHERE id = %s"
        try:
            self.db.execute_query(query, (id,))
            self.logger.info("Employee deleted", id=id)
            return True
        except Exception as e:
            self.logger.error("Database error while deleting employee", id=id, error=str(e))
            raise DatabaseError(f"Failed to delete employee {id}: {str(e)}")
