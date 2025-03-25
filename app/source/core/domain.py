from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from typing import Optional

@dataclass
class Company:
    """회사 정보"""
    id: str
    company_name: str
    biz_id: str
    email: Optional[str] = None
    rep_name: Optional[str] = None
    address: Optional[str] = None
    biz_type: Optional[str] = None
    biz_item: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    rep_stamp: Optional[str] = None

@dataclass
class Employee:
    """직원 정보"""
    id: str
    name: str
    email: str  
    jira_account_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    signature: Optional[str] = None
    stamp: Optional[str] = None 
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    fax: Optional[str] = None

@dataclass
class Research:
    """연구 과제 정보"""
    id: str
    project_name: str
    project_code: str
    project_period: Optional[str] = None
    project_manager: Optional[str] = None
    project_start_date: Optional[date] = None
    project_end_date: Optional[date] = None
    budget: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None

@dataclass
class Expert:
    """전문가 정보"""
    id: str
    name: str
    affiliation: Optional[str] = None
    position: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    classification: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    specialty: Optional[str] = None
    bio: Optional[str] = None


