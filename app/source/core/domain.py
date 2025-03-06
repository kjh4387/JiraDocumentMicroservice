from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any

@dataclass
class Company:
    """회사 정보"""
    id: str
    company_name: str
    biz_id: str
    rep_name: Optional[str] = None
    address: Optional[str] = None
    biz_type: Optional[str] = None
    biz_item: Optional[str] = None
    phone: Optional[str] = None
    rep_stamp: Optional[str] = None

@dataclass
class Employee:
    """직원 정보"""
    id: str
    name: str
    department: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    signature: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None

@dataclass
class Research:
    """연구 과제 정보"""
    id: str
    project_name: str
    project_period: Optional[str] = None
    project_manager: Optional[str] = None
    project_code: Optional[str] = None

@dataclass
class Expert:
    """전문가 정보"""
    id: str
    name: str
    affiliation: Optional[str] = None
    position: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    classification: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

@dataclass
class DocumentSection:
    """문서 섹션 기본 클래스"""
    section_type: str
    data: Dict[str, Any]

@dataclass
class Document:
    """문서 기본 클래스"""
    id: str
    document_type: str
    created_at: date = field(default_factory=date.today)
    updated_at: date = field(default_factory=date.today)
    sections: List[DocumentSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
