import os
import base64
from typing import Optional
from app.source.core.interfaces import Repository
from app.source.core.domain import Employee
from app.source.core.logging import get_logger

logger = get_logger(__name__)

class SignatureService:
    """서명 이미지 관리 서비스"""
    
    def __init__(self, signature_dir: str, employee_repo: Repository[Employee]):
        """초기화"""
        self.signature_dir = signature_dir
        self.employee_repo = employee_repo
        
        # 서명 디렉토리 생성
        os.makedirs(signature_dir, exist_ok=True)
        logger.debug("SignatureService initialized", signature_dir=signature_dir)
    
    def save_signature(self, employee_id: str, signature_data: str) -> str:
        """서명 이미지 저장"""
        logger.debug("Saving signature", employee_id=employee_id)
        
        # 직원 확인
        employee = self.employee_repo.find_by_id(employee_id)
        if not employee:
            logger.error("Employee not found", employee_id=employee_id)
            raise ValueError(f"Employee not found: {employee_id}")
        
        # Base64 데이터인 경우 디코딩
        if signature_data.startswith('data:image'):
            signature_data = signature_data.split(',')[1]
            image_data = base64.b64decode(signature_data)
            
            # 파일로 저장
            file_path = os.path.join(self.signature_dir, f"{employee_id}.png")
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            # 직원 정보 업데이트
            employee.signature = file_path
            self.employee_repo.save(employee)
            
            logger.info("Signature saved", employee_id=employee_id, file_path=file_path)
            return file_path
        
        # 이미 파일 경로인 경우 그대로 반환
        logger.info("Signature path saved", employee_id=employee_id, file_path=signature_data)
        return signature_data
    
    def get_signature(self, employee_id: str) -> Optional[str]:
        """서명 이미지 조회"""
        logger.debug("Getting signature", employee_id=employee_id)
        
        # 직원 확인
        employee = self.employee_repo.find_by_id(employee_id)
        if not employee:
            logger.warning("Employee not found", employee_id=employee_id)
            return None
        
        # 서명 이미지가 있으면 반환
        if employee.signature:
            logger.debug("Signature found in employee record", employee_id=employee_id)
            return employee.signature
        
        # 파일 시스템에서 확인
        file_path = os.path.join(self.signature_dir, f"{employee_id}.png")
        if os.path.exists(file_path):
            # 직원 정보 업데이트
            employee.signature = file_path
            self.employee_repo.save(employee)
            
            logger.debug("Signature found in file system", employee_id=employee_id, file_path=file_path)
            return file_path
        
        logger.warning("Signature not found", employee_id=employee_id)
        return None
    
    def get_signature_as_base64(self, employee_id: str) -> Optional[str]:
        """서명 이미지를 Base64로 인코딩하여 반환"""
        logger.debug("Getting signature as base64", employee_id=employee_id)
        
        # 서명 이미지 경로 조회
        signature_path = self.get_signature(employee_id)
        if not signature_path:
            logger.warning("Signature not found", employee_id=employee_id)
            return None
        
        # 이미 Base64 형식이면 그대로 반환
        if signature_path.startswith('data:image'):
            logger.debug("Signature already in base64 format", employee_id=employee_id)
            return signature_path
        
        # 파일을 Base64로 인코딩
        try:
            with open(signature_path, 'rb') as f:
                image_data = f.read()
            
            base64_data = base64.b64encode(image_data).decode('utf-8')
            result = f"data:image/png;base64,{base64_data}"
            
            logger.debug("Signature converted to base64", employee_id=employee_id)
            return result
        except Exception as e:
            logger.error("Failed to convert signature to base64", 
                        employee_id=employee_id, error=str(e))
            return None
    
    def delete_signature(self, employee_id: str) -> bool:
        """서명 이미지 삭제"""
        logger.debug("Deleting signature", employee_id=employee_id)
        
        # 직원 확인
        employee = self.employee_repo.find_by_id(employee_id)
        if not employee:
            logger.warning("Employee not found", employee_id=employee_id)
            return False
        
        # 서명 이미지 경로 확인
        signature_path = employee.signature
        if not signature_path:
            logger.warning("No signature to delete", employee_id=employee_id)
            return False
        
        # 파일 삭제
        if os.path.exists(signature_path):
            try:
                os.remove(signature_path)
                logger.debug("Signature file deleted", employee_id=employee_id, file_path=signature_path)
            except Exception as e:
                logger.error("Failed to delete signature file", 
                            employee_id=employee_id, file_path=signature_path, error=str(e))
                return False
        
        # 직원 정보 업데이트
        employee.signature = None
        self.employee_repo.save(employee)
        
        logger.info("Signature deleted", employee_id=employee_id)
        return True
