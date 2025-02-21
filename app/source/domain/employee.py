import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection
import domain.bank_account as bank_account

class Employee:
    def __init__(self, name: str, email: str, bank_account: bank_account, department: str, position: str, affiliation_id, signature_path: str): 
        """
        Args:
            name (str): 직원 이름
            email (str): 직원 이메일
            bank_account (bank_account): 직원 은행 계좌
            department (str): 직원 부서
            position (str): 직원 직급
            affiliation_id: 소속 회사 ID
            signature_path (str): 직원 서명 이미지 경로
        """
        self.name = name          
        self.email = email
        self.department = department
        self.position = position
        self.affiliation_id = affiliation_id
        self.signature_path = signature_path

