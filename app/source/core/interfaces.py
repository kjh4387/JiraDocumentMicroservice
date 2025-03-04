from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Tuple

T = TypeVar('T')

class Repository(Generic[T], ABC):
    """저장소 인터페이스"""
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        """ID로 엔티티 조회"""
        pass
    
    @abstractmethod
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """조건에 맞는 엔티티 목록 조회"""
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """엔티티 저장"""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """엔티티 삭제"""
        pass

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """단일 문서 조회"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def find_many(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """여러 문서 조회"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def insert_one(self, document: Dict[str, Any]) -> str:
        """단일 문서 저장"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """단일 문서 업데이트"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def delete_one(self, query: Dict[str, Any]) -> bool:
        """단일 문서 삭제"""
        raise NotImplementedError("Subclasses must implement this method")

class UnitOfWork(ABC):
    """단위 작업 인터페이스"""
    
    @abstractmethod
    def __enter__(self):
        """트랜잭션 시작"""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """트랜잭션 종료"""
        pass
    
    @abstractmethod
    def commit(self):
        """변경사항 커밋"""
        pass
    
    @abstractmethod
    def rollback(self):
        """변경사항 롤백"""
        pass

class SchemaValidator(ABC):
    """스키마 검증 인터페이스"""
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """데이터가 스키마에 맞는지 검증"""
        pass
    
    @abstractmethod
    def validate_document_type(self, document_type: str) -> bool:
        """문서 유형이 유효한지 검증"""
        pass

class DataEnricher(ABC):
    """데이터 보강 인터페이스"""
    
    @abstractmethod
    def enrich(self, document_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 데이터 보강"""
        pass

class SectionRenderer(ABC):
    """섹션 렌더링 인터페이스"""
    
    @abstractmethod
    def render_section(self, document_type: str, section_name: str, section_data: Dict[str, Any]) -> str:
        """섹션 렌더링"""
        pass

class DocumentRenderer(ABC):
    """문서 렌더링 인터페이스"""
    
    @abstractmethod
    def render(self, document_type: str, data: Dict[str, Any]) -> str:
        """문서 데이터를 HTML로 렌더링"""
        pass

class PdfGenerator(ABC):
    """PDF 생성 인터페이스"""
    
    @abstractmethod
    def generate(self, html: str) -> bytes:
        """HTML을 PDF로 변환"""
        pass

class Logger(ABC):
    """로깅 인터페이스"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs):
        """정보 로그"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs):
        """경고 로그"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs):
        """오류 로그"""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs):
        """심각한 오류 로그"""
        pass
