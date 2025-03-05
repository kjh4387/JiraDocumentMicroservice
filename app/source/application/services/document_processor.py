from typing import Dict, Any, List, Optional
from app.source.core.logging import get_logger
from app.source.core.interfaces import Repository
import copy

logger = get_logger(__name__)

class ConfigurableDocumentProcessor:
    """설정 기반 문서 처리기"""
    
    def __init__(self, schema_registry, field_processors, repositories):
        self.schema_registry = schema_registry
        self.field_processors = field_processors
        self.repositories = repositories
        self.post_processors = {}  # 문서 유형별 후처리기
    
    def register_post_processor(self, processor_name, processor):
        """후처리기 등록"""
        self.post_processors[processor_name] = processor
    
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """문서 처리 메인 메서드"""
        document_type = request.get("document_type")
        direct_data = request.get("direct_data", {})
        reference_data = request.get("reference_data", {})
        
        # 1. 문서 유형별 설정 로드
        document_config = self.schema_registry.get_document_config(document_type)
        
        # 2. 직접 데이터 처리
        processed_direct = self._process_direct_data(
            document_type, 
            direct_data, 
            document_config
        )
        
        # 3. 참조 데이터 처리
        processed_reference = self._process_reference_data(
            document_type,
            reference_data,
            document_config
        )
        
        # 4. 결과 병합
        result = {
            "document_type": document_type,
            **processed_direct,
            **processed_reference
        }
        
        # 5. 문서 유형별 후처리 규칙 적용
        if "post_processors" in document_config:
            for processor_name in document_config["post_processors"]:
                if processor_name in self.post_processors:
                    post_processor = self.post_processors[processor_name]
                    result = post_processor.process(result)
                else:
                    logger.warning(f"Post processor not found: {processor_name}")
        
        return result
    
    def _process_direct_data(self, 
                             document_type: str, 
                             direct_data: Dict[str, Any],
                             document_config: Dict[str, Any]) -> Dict[str, Any]:
        """직접 데이터 처리"""
        result = {}
        
        if "direct_fields" not in document_config:
            logger.warning(f"No direct fields config for document type: {document_type}")
            return direct_data.copy()  # 설정이 없으면 원본 반환
        
        # 스키마에 따라 필드 처리
        field_specs = document_config["direct_fields"]
        for field_name, field_spec in field_specs.items():
            field_type = field_spec.get("type", "string")
            required = field_spec.get("required", False)
            
            # 필수 필드 검증
            if required and field_name not in direct_data:
                logger.error(f"Required field missing: {field_name}")
                # 여기서 예외를 발생시키거나 기본값을 사용할 수 있음
                continue
                
            # 필드가 존재하면 처리
            if field_name in direct_data:
                field_value = direct_data[field_name]
                
                # 필드 타입별 처리기 사용
                if field_type in self.field_processors:
                    processor = self.field_processors[field_type]
                    processed_value = processor.process(field_value, field_spec)
                    result[field_name] = processed_value
                else:
                    # 처리기가 없으면 원본 값 사용
                    result[field_name] = field_value
        
        # 스키마에 없는 추가 필드도 포함
        for field_name, field_value in direct_data.items():
            if field_name not in field_specs and field_name not in result:
                result[field_name] = field_value
        
        return result
    
    def _process_reference_data(self, 
                                document_type: str,
                                reference_data: Dict[str, Any],
                                document_config: Dict[str, Any]) -> Dict[str, Any]:
        """참조 데이터 처리"""
        result = {}
        
        if "reference_fields" not in document_config:
            logger.warning(f"No reference fields config for document type: {document_type}")
            return {}
        
        # 참조 필드 처리
        for field_mapping in document_config["reference_fields"]:
            field = field_mapping.get("field")
            entity_type = field_mapping.get("entity_type")
            lookup_field = field_mapping.get("lookup_field")
            target_path = field_mapping.get("target_path")
            fields = field_mapping.get("fields", [])
            is_array = field_mapping.get("is_array", False)
            
            if not all([field, entity_type, lookup_field, target_path]):
                logger.warning(f"Invalid reference field mapping: {field_mapping}")
                continue
            
            # 참조 필드가 없으면 스킵
            if field not in reference_data:
                logger.debug(f"Reference field not in request: {field}")
                continue
            
            # 참조 데이터 값 가져오기
            reference_value = reference_data[field]
            
            # 배열 필드 처리
            if is_array:
                if not isinstance(reference_value, list):
                    logger.warning(f"Expected array for field {field}, got {type(reference_value)}")
                    continue
                
                processed_items = []
                for item in reference_value:
                    # 리스트 항목이 딕셔너리가 아니면 스킵
                    if not isinstance(item, dict):
                        continue
                    
                    # 조회 필드가 항목에 없으면 스킵
                    if lookup_field not in item:
                        continue
                    
                    lookup_value = item[lookup_field]
                    entity = self._fetch_entity(entity_type, lookup_field, lookup_value)
                    
                    if entity:
                        # 필요한 필드만 추출
                        entity_data = {f: entity.get(f) for f in fields if f in entity}
                        
                        # 원본 항목의 추가 데이터 병합
                        for k, v in item.items():
                            if k != lookup_field and k not in entity_data:
                                entity_data[k] = v
                        
                        processed_items.append(entity_data)
                
                # 후처리 적용
                additional_processing = field_mapping.get("additional_processing")
                if additional_processing and hasattr(self, f"_apply_{additional_processing}"):
                    process_method = getattr(self, f"_apply_{additional_processing}")
                    processed_items = process_method(processed_items)
                
                # 결과에 추가
                self._set_nested_value(result, target_path, processed_items)
            
            # 단일 필드 처리
            else:
                lookup_value = reference_value
                entity = self._fetch_entity(entity_type, lookup_field, lookup_value)
                
                if entity:
                    # 필요한 필드만 추출
                    entity_data = {f: entity.get(f) for f in fields if f in entity}
                    
                    # 결과에 추가
                    self._set_nested_value(result, target_path, entity_data)
        
        return result
    
    def _fetch_entity(self, entity_type: str, lookup_field: str, value: Any) -> Optional[Dict[str, Any]]:
        """엔티티 조회"""
        if entity_type not in self.repositories:
            logger.warning(f"Repository not found for entity type: {entity_type}")
            return None
        
        repository = self.repositories[entity_type]
        try:
            query = {lookup_field: value}
            entity = repository.find_one(query)
            return entity
        except Exception as e:
            logger.error(f"Failed to fetch entity", 
                        entity_type=entity_type, 
                        lookup_field=lookup_field, 
                        value=value,
                        error=str(e))
            return None
    
    def _set_nested_value(self, obj: Dict[str, Any], path: str, value: Any) -> None:
        """중첩 경로에 값 설정"""
        parts = path.split('.')
        for i, part in enumerate(parts[:-1]):
            if part not in obj:
                obj[part] = {}
            obj = obj[part]
        obj[parts[-1]] = value
    
    # 추가 처리 메서드들
    def _apply_add_approval_order(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """승인 순서 추가 처리"""
        # 이미 order 필드가 있으면 그것으로 정렬
        if items and any("order" in item for item in items):
            return sorted(items, key=lambda x: x.get("order", 99))
        
        # 없으면 리스트 순서대로 order 부여
        for i, item in enumerate(items):
            item["order"] = i + 1
        return items 