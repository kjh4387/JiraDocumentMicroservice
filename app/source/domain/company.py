import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection
import domain.bank_account as bank_account

class Company:
    def __init__(self, id, name: str, email: str, bank_account: bank_account, address, phone_number): 
        """
        id: 회사 ID
        name (str): 회사 이름
        email (str): 회사 이메일
        bank_account (bank_account): 회사 은행 계좌
        address (str): 회사 주소
        phone_number (str): 회사 전화번호
        """
        self.id = id
        self.name = name          
        self.email = email
        self.bank_account = bank_account
        self.address = address
        self.phone_number = phone_number