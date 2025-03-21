class DocumentAutomationError(Exception):
    """문서 자동화 시스템 기본 예외"""
    pass

class ValidationError(DocumentAutomationError):
    """데이터 검증 오류"""
    pass

class RenderingError(DocumentAutomationError):
    """렌더링 오류"""
    pass

class PdfGenerationError(DocumentAutomationError):
    """PDF 생성 오류"""
    pass

class RepositoryError(DocumentAutomationError):
    """저장소 오류"""
    pass

class EntityNotFoundError(RepositoryError):
    """엔티티를 찾을 수 없음"""
    pass

class DatabaseError(RepositoryError):
    """데이터베이스 오류"""
    pass

class SchemaError(DocumentAutomationError):
    """스키마 오류"""
    pass

class ConfigurationError(DocumentAutomationError):
    """설정 오류"""
    pass

class MappingError(DocumentAutomationError):
    """매핑 오류"""
    pass
