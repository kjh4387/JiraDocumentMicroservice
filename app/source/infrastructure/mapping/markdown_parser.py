from typing import List, Dict, Any
import re

class MarkdownTableParser:
    """마크다운 테이블을 파싱하는 유틸리티 클래스"""
    
    @staticmethod
    def parse_table(markdown_text: str) -> List[Dict[str, str]]:
        """
        마크다운 테이블을 파싱하여 딕셔너리 리스트로 변환
        
        Args:
            markdown_text (str): 마크다운 테이블 텍스트
            
        Returns:
            List[Dict[str, str]]: 파싱된 데이터의 리스트
        """
        if not markdown_text:
            return []
            
        # 줄 단위로 분리
        lines = markdown_text.strip().split('\n')
        if len(lines) < 2:
            return []
            
        # 헤더 추출 및 정리
        headers = [h.strip() for h in lines[0].strip('|').split('|')]
        
        # 구분선 제거 (두 번째 줄)
        
        # 데이터 행 처리
        result = []
        for line in lines[1:]:  # 구분선 이후의 행들만 처리
            if not line.strip():  # 빈 줄 무시
                continue
            values = [v.strip() for v in line.strip('|').split('|')]
            if len(values) == len(headers):
                row_dict = dict(zip(headers, values))
                if any(row_dict.values()):  # 모든 값이 비어있지 않은 경우만 추가
                    result.append(row_dict)
                    
        return result 