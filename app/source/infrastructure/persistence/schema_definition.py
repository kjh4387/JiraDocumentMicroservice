"""
데이터베이스 스키마 정의 및 관리 모듈
단일 진실 원천(Single Source of Truth) 패턴을 적용하여
도메인 모델과 데이터베이스 스키마 간 일관성을 유지합니다.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import logging

logger = logging.getLogger(__name__)

class ColumnDefinition:
    """데이터베이스 컬럼 정의"""
    def __init__(self, name: str, data_type: str, nullable: bool = True, 
                 primary_key: bool = False, unique: bool = False, default=None):
        self.name = name
        self.data_type = data_type
        self.nullable = nullable
        self.primary_key = primary_key
        self.unique = unique
        self.default = default
        
    def get_sql_definition(self) -> str:
        """컬럼 SQL 정의 반환"""
        sql = f"{self.name} {self.data_type}"
        
        if self.primary_key:
            sql += " PRIMARY KEY"
        if not self.nullable:
            sql += " NOT NULL"
        if self.unique:
            sql += " UNIQUE"
        if self.default is not None:
            sql += f" DEFAULT {self.default}"
            
        return sql
        
    def __str__(self) -> str:
        return self.get_sql_definition()


class TableSchema:
    """데이터베이스 테이블 스키마 정의"""
    def __init__(self, table_name: str, columns: List[ColumnDefinition], logger=None):
        self.table_name = table_name
        self.columns = columns
        self.logger = logger or logging.getLogger(__name__)
        self._validate_schema()
        self.logger.debug(f"TableSchema created for {table_name}")
        
    def _validate_schema(self) -> None:
        """스키마 유효성 검증"""
        # 기본 키가 하나만 존재하는지 확인
        primary_keys = [col for col in self.columns if col.primary_key]
        if len(primary_keys) != 1:
            raise ValueError(f"Table {self.table_name} must have exactly one primary key")
            
        # 컬럼 이름이 중복되지 않는지 확인
        column_names = [col.name for col in self.columns]
        if len(column_names) != len(set(column_names)):
            raise ValueError(f"Table {self.table_name} has duplicate column names")
    
    @property
    def primary_key(self) -> ColumnDefinition:
        """기본 키 컬럼 반환"""
        for col in self.columns:
            if col.primary_key:
                return col
        # 유효성 검증에서 확인하므로 여기까지 오면 안됨
        raise ValueError("No primary key found")
    
    @property
    def column_names(self) -> List[str]:
        """모든 컬럼 이름 목록 반환"""
        return [col.name for col in self.columns]
    
    def get_column_by_name(self, name: str) -> Optional[ColumnDefinition]:
        """이름으로 컬럼 찾기"""
        for col in self.columns:
            if col.name == name:
                return col
        return None
    
    def create_table_sql(self) -> str:
        """테이블 생성 SQL 생성"""
        column_defs = [col.get_sql_definition() for col in self.columns]
        sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                {', '.join(column_defs)}
            )
        """
        return sql
    
    def insert_sql(self) -> str:
        """INSERT SQL 템플릿 생성"""
        columns = ', '.join(self.column_names)
        placeholders = ', '.join(['%s'] * len(self.column_names))
        return f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
    
    def update_sql(self) -> str:
        """UPDATE SQL 템플릿 생성"""
        set_clause = ', '.join([f"{col} = %s" for col in self.column_names if col != self.primary_key.name])
        return f"UPDATE {self.table_name} SET {set_clause} WHERE {self.primary_key.name} = %s"
    
    def select_by_id_sql(self) -> str:
        """ID로 SELECT SQL 생성"""
        columns = ', '.join(self.column_names)
        return f"SELECT {columns} FROM {self.table_name} WHERE {self.primary_key.name} = %s"
    
    def select_by_criteria_sql(self, criteria: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """조건으로 SELECT SQL 생성"""
        columns = ', '.join(self.column_names)
        where_clauses = []
        params = []
        
        for key, value in criteria.items():
            if key in self.column_names:
                where_clauses.append(f"{key} = %s")
                params.append(value)
        
        where_clause = ' AND '.join(where_clauses)
        return f"SELECT {columns} FROM {self.table_name} WHERE {where_clause}", params
    
    def delete_sql(self) -> str:
        """DELETE SQL 템플릿 생성"""
        return f"DELETE FROM {self.table_name} WHERE {self.primary_key.name} = %s"
    
    def get_insert_params(self, entity: Any) -> List[Any]:
        """엔티티에서 INSERT 파라미터 추출"""
        return [getattr(entity, col.name) for col in self.columns]
    
    def get_update_params(self, entity: Any) -> List[Any]:
        """엔티티에서 UPDATE 파라미터 추출"""
        # SET 절 파라미터 + WHERE 조건의 ID 값
        params = [getattr(entity, col.name) for col in self.columns if col.name != self.primary_key.name]
        params.append(getattr(entity, self.primary_key.name))
        return params


# 도메인 모델 기반 스키마 정의
def create_company_schema() -> TableSchema:
    """회사 테이블 스키마 생성"""
    columns = [
        ColumnDefinition("id", "VARCHAR(50)", nullable=False, primary_key=True),
        ColumnDefinition("company_name", "VARCHAR(100)", nullable=False),
        ColumnDefinition("biz_id", "VARCHAR(20)", nullable=False),
        ColumnDefinition("email", "VARCHAR(100)"),
        ColumnDefinition("rep_name", "VARCHAR(50)"),
        ColumnDefinition("address", "VARCHAR(200)"),
        ColumnDefinition("biz_type", "VARCHAR(50)"),
        ColumnDefinition("biz_item", "VARCHAR(100)"),
        ColumnDefinition("phone", "VARCHAR(20)"),
        ColumnDefinition("fax", "VARCHAR(20)"),
        ColumnDefinition("rep_stamp", "TEXT")
    ]
    return TableSchema("companies", columns)

def create_employee_schema() -> TableSchema:
    """직원 테이블 스키마 생성"""
    columns = [
        ColumnDefinition("id", "VARCHAR(50)", nullable=False, primary_key=True),
        ColumnDefinition("name", "VARCHAR(50)", nullable=False),
        ColumnDefinition("email", "VARCHAR(100)", nullable=False),
        ColumnDefinition("jira_account_id", "VARCHAR(100)"),
        ColumnDefinition("department", "VARCHAR(50)"),
        ColumnDefinition("position", "VARCHAR(50)"),
        ColumnDefinition("phone", "VARCHAR(20)"),
        ColumnDefinition("signature", "TEXT"),
        ColumnDefinition("stamp", "TEXT"),
        ColumnDefinition("bank_name", "VARCHAR(50)"),
        ColumnDefinition("account_number", "VARCHAR(50)"),
        ColumnDefinition("birth_date", "DATE"),
        ColumnDefinition("address", "VARCHAR(200)"),
        ColumnDefinition("fax", "VARCHAR(20)")
    ]
    return TableSchema("employees", columns)

def create_research_schema() -> TableSchema:
    """연구 과제 테이블 스키마 생성"""
    columns = [
        ColumnDefinition("id", "VARCHAR(50)", nullable=False, primary_key=True),
        ColumnDefinition("project_name", "VARCHAR(100)", nullable=False),
        ColumnDefinition("project_code", "VARCHAR(50)", nullable=False),
        ColumnDefinition("project_period", "VARCHAR(100)"),
        ColumnDefinition("project_manager", "VARCHAR(50)"),
        ColumnDefinition("project_start_date", "DATE"),
        ColumnDefinition("project_end_date", "DATE"),
        ColumnDefinition("budget", "INTEGER"),
        ColumnDefinition("status", "VARCHAR(20)")
    ]
    return TableSchema("research_projects", columns)

def create_expert_schema() -> TableSchema:
    """전문가 테이블 스키마 생성"""
    columns = [
        ColumnDefinition("id", "VARCHAR(50)", nullable=False, primary_key=True),
        ColumnDefinition("name", "VARCHAR(50)", nullable=False),
        ColumnDefinition("affiliation", "VARCHAR(100)"),
        ColumnDefinition("position", "VARCHAR(50)"),
        ColumnDefinition("email", "VARCHAR(100)"),
        ColumnDefinition("phone", "VARCHAR(20)"),
        ColumnDefinition("specialty", "VARCHAR(100)")
    ]
    return TableSchema("experts", columns)

# 스키마 등록 및 관리
class SchemaRegistry:
    """스키마 레지스트리 - 모든 스키마를 중앙에서 관리"""
    _schemas: Dict[str, TableSchema] = {}
    _logger = None
    
    @classmethod
    def set_logger(cls, logger):
        """로거 설정"""
        cls._logger = logger
    
    @classmethod
    def get_logger(cls):
        """로거 가져오기"""
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger
    
    @classmethod
    def register(cls, schema: TableSchema) -> None:
        """스키마 등록"""
        cls._schemas[schema.table_name] = schema
        cls.get_logger().debug(f"Schema registered: {schema.table_name}")
    
    @classmethod
    def get(cls, table_name: str) -> Optional[TableSchema]:
        """테이블명으로 스키마 조회"""
        return cls._schemas.get(table_name)
    
    @classmethod
    def get_all(cls) -> Dict[str, TableSchema]:
        """모든 스키마 조회"""
        return cls._schemas.copy()
    
    @classmethod
    def generate_create_all_tables_sql(cls) -> str:
        """모든 테이블 생성 SQL 생성"""
        sql_statements = [schema.create_table_sql() for schema in cls._schemas.values()]
        return '\n'.join(sql_statements)

# 스키마 등록
SchemaRegistry.register(create_company_schema())
SchemaRegistry.register(create_employee_schema())
SchemaRegistry.register(create_research_schema())
SchemaRegistry.register(create_expert_schema()) 