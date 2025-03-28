from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentMetadataDTO(BaseModel):
    """문서 메타데이터 DTO"""
    document_number: str = Field(..., description="문서 번호")
    date_issued: str = Field(..., description="발행일자")
    receiver: Optional[str] = Field(None, description="수신자")
    reference: Optional[str] = Field(None, description="참조")

class SupplierInfoDTO(BaseModel):
    """공급자 정보 DTO"""
    company_id: str = Field(..., description="회사 ID")
    company_name: Optional[str] = Field(None, description="회사명")
    biz_id: Optional[str] = Field(None, description="사업자등록번호")
    rep_name: Optional[str] = Field(None, description="대표자명")
    address: Optional[str] = Field(None, description="주소")
    biz_type: Optional[str] = Field(None, description="업태")
    biz_item: Optional[str] = Field(None, description="종목")
    phone: Optional[str] = Field(None, description="전화번호")

class ItemDTO(BaseModel):
    """품목 DTO"""
    name: str = Field(..., description="품명")
    spec: Optional[str] = Field(None, description="규격")
    quantity: int = Field(..., description="수량")
    unit_price: int = Field(..., description="단가")
    amount: int = Field(..., description="공급가액")
    vat: Optional[int] = Field(None, description="세액")
    memo: Optional[str] = Field(None, description="비고")

class AmountSummaryDTO(BaseModel):
    """금액 요약 DTO"""
    supply_sum: int = Field(..., description="공급가액 합계")
    vat_sum: int = Field(..., description="세액 합계")
    grand_total: int = Field(..., description="총액")

class ParticipantDTO(BaseModel):
    """참가자 DTO"""
    email: str = Field(..., description="이메일")
    employee_id: Optional[str] = Field(None, description="직원 ID")
    name: Optional[str] = Field(None, description="이름")
    department: Optional[str] = Field(None, description="부서")
    position: Optional[str] = Field(None, description="직위")
    phone: Optional[str] = Field(None, description="연락처")

class ResearchProjectInfoDTO(BaseModel):
    """연구 과제 정보 DTO"""
    project_code: str = Field(..., description="과제 코드")
    project_id: Optional[str] = Field(None, description="과제 ID")
    project_name: Optional[str] = Field(None, description="과제명")
    project_period: Optional[str] = Field(None, description="과제 기간")
    project_manager: Optional[str] = Field(None, description="과제 책임자")

class TravelInfoDTO(BaseModel):
    """출장 정보 DTO"""
    employee_id: str = Field(..., description="직원 ID")
    name: Optional[str] = Field(None, description="이름")
    purpose: str = Field(..., description="출장 목적")
    duration: str = Field(..., description="출장 기간")
    destination: str = Field(..., description="출장지")

class ExpertInfoDTO(BaseModel):
    """전문가 정보 DTO"""
    expert_id: str = Field(..., description="전문가 ID")
    name: Optional[str] = Field(None, description="이름")
    affiliation: Optional[str] = Field(None, description="소속")
    position: Optional[str] = Field(None, description="직위")
    dob: Optional[str] = Field(None, description="생년월일")
    address: Optional[str] = Field(None, description="주소")
    classification: Optional[str] = Field(None, description="구분")
    email: Optional[str] = Field(None, description="이메일")
    phone: Optional[str] = Field(None, description="연락처")

class ApproverDTO(BaseModel):
    """결재자 DTO"""
    email: str = Field(..., description="이메일")
    employee_id: Optional[str] = Field(None, description="직원 ID")
    name: Optional[str] = Field(None, description="이름")
    position: Optional[str] = Field(None, description="직위")
    department: Optional[str] = Field(None, description="부서")
    approval_status: Optional[str] = Field(None, description="결재 상태")
    approval_date: Optional[str] = Field(None, description="결재 일시")
    comment: Optional[str] = Field(None, description="결재 의견")
    signature: Optional[str] = Field(None, description="서명 이미지")

class DocumentResponseDTO(BaseModel):
    """문서 응답 DTO"""
    document_id: str = Field(..., description="문서 ID")
    document_type: str = Field(..., description="문서 유형")
    created_at: datetime = Field(..., description="생성 시간")
    html: Optional[str] = Field(None, description="HTML 내용")
    pdf_url: Optional[str] = Field(None, description="PDF 파일 URL")

class DocumentRequestDTO(BaseModel):
    """문서 요청 DTO"""
    issue_key: str = Field(..., description="Jira 이슈 키")
    
    class Config:
        """Pydantic 설정"""
        extra = "allow"  # 추가 필드 허용
