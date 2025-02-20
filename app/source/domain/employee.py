import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection
import domain.bank_account as bank_account

class Employee:
    def __init__(self, name: str, email: str, bank_account: bank_account, department: str, position: str, signature_path: str): 
        self.name = name          
        self.email = email
        self.department = department
        self.position = position
        self.signature_path = signature_path

