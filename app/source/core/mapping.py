# 필드 매핑 정의
FIELD_MAPPINGS = {
    "출장신청서": {
        "applicant": {
            "lookup_field": "email",
            "target_fields": ["employee_name", "department", "position"]
        },
        "travel_list": {
            "lookup_field": "email",
            "target_fields": ["employee_name", "department", "position"]
        }
    },
    "회의록": {
        "participants": {
            "lookup_field": "email",
            "target_fields": ["name", "department", "position"]
        }
    }
}

class FieldMapper:
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def map_fields(self, document_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """문서 데이터의 필드 매핑 처리"""
        if document_type not in FIELD_MAPPINGS:
            return data
        
        mappings = FIELD_MAPPINGS[document_type]
        
        # 섹션 데이터 순회
        for section in data.get("sections", []):
            section_type = section.get("section_type")
            
            if section_type in mappings:
                mapping_info = mappings[section_type]
                section_data = section.get("data", {})
                
                # 단일 객체인 경우
                if isinstance(section_data, dict):
                    self._process_mapping(section_data, mapping_info)
                
                # 배열인 경우
                elif isinstance(section_data, list):
                    for item in section_data:
                        self._process_mapping(item, mapping_info)
        
        return data
    
    def _process_mapping(self, data: Dict[str, Any], mapping_info: Dict[str, Any]) -> None:
        """개별 데이터 항목의 매핑 처리"""
        lookup_field = mapping_info["lookup_field"]
        target_fields = mapping_info["target_fields"]
        
        if lookup_field in data:
            lookup_value = data[lookup_field]
            entity = self._get_entity_by_field(lookup_field, lookup_value)
            
            if entity:
                for field in target_fields:
                    if field in entity:
                        data[field] = entity[field]
    
    def _get_entity_by_field(self, field: str, value: Any) -> Dict[str, Any]:
        """필드 값으로 엔티티 조회"""
        try:
            query = {field: value}
            entity = self.user_repository.find_one(query)
            return entity
        except Exception as e:
            logger.error(f"Failed to get entity by {field}: {value}", error=str(e))
            return {} 