from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Tuple

T = TypeVar('T')

class JiraClient(ABC):
    """Jira 클라이언트 인터페이스"""
    
    @abstractmethod
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """이슈 정보 조회"""
        pass
    
    @abstractmethod
    def download_attachments(self, issue_key: str) -> List[str]:
        """첨부 파일 다운로드"""
        pass
    
    @abstractmethod
    def get_issue_fields(self, issue_key: str) -> Dict[str, Any]:
        """이슈 필드 조회"""
        pass

class JiraFieldMapper(ABC):
    """Jira 필드 매핑 인터페이스"""
    
    @abstractmethod
    def map_field_id_to_name(field_id: str) -> str:
        """필드 ID를 이름으로 변환"""
        pass

    @abstractmethod
    def map_field_name_to_id(field_name: str) -> str:
        """필드 이름을 ID로 변환"""
        pass

    @abstractmethod
    def transform_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """응답 데이터 변환"""
        pass

    @abstractmethod
    def set_mapping_provider(self, provider):
        """매핑 제공자 설정"""
        pass

class JiraFieldMappingProvider(ABC):
    """Jira 필드 매핑 제공자 인터페이스"""
    
    @abstractmethod
    def get_field_mapping(self) -> Dict[str, Any]:
        """필드 매핑 가져오기"""
        pass

    @abstractmethod
    def refresh(self)->None:
        """매핑 새로고침"""
        pass   


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

class DocumentGenerationStrategy(ABC):
    """문서 생성 전략 인터페이스"""
    
    @abstractmethod
    def generate_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 생성
        
        Args:
            data: 문서 데이터
            
        Returns:
            생성된 문서 정보
        """
        pass
