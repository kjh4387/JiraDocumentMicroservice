import json
import os
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

# 템플릿 환경 설정
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = BASE_DIR / 'templates'

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

def test_estimate_template():
    """견적서 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "견적서",
        "metadata": {
            "document_number": "EST-2023-001",
            "date_issued": "2023-05-15",
            "receiver": "ABC 주식회사"
        },
        "supplier_info": {
            "company_name": "XYZ 주식회사",
            "address": "서울시 강남구 테헤란로 123",
            "rep_name": "홍길동",
            "phone": "02-1234-5678"
        },
        "item_list": [
            {
                "name": "소프트웨어 개발",
                "quantity": 1,
                "unit_price": 1000000
            },
            {
                "name": "서버 유지보수",
                "quantity": 2,
                "unit_price": 500000
            }
        ]
    }
    
    # 템플릿 렌더링
    template = env.get_template('estimate.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "견적서" in result
    assert data["metadata"]["document_number"] in result
    assert data["metadata"]["date_issued"] in result
    assert data["metadata"]["receiver"] in result
    assert data["supplier_info"]["company_name"] in result
    
    # 합계 확인 (namespace 변수 확인)
    # 첫 번째 항목: 1 * 1000000 = 1000000, VAT: 100000, 합계: 1100000
    # 두 번째 항목: 2 * 500000 = 1000000, VAT: 100000, 합계: 1100000
    # 전체 합계: 2000000 + 200000 = 2200000
    assert "2000000" in result  # 공급가액 합계
    assert "200000" in result   # 세액 합계
    assert "2200000" in result  # 총 합계

def test_transaction_template():
    """거래명세서 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "거래명세서",
        "metadata": {
            "document_number": "TR-2023-001",
            "date_issued": "2023-05-20",
            "receiver": "DEF 주식회사"
        },
        "supplier_info": {
            "company_name": "XYZ 주식회사",
            "address": "서울시 강남구 테헤란로 123",
            "rep_name": "홍길동",
            "phone": "02-1234-5678"
        },
        "customer_info": {
            "company_id": "CUST-001",
            "company_name": "DEF 주식회사",
            "address": "서울시 서초구 반포대로 45",
            "rep_name": "김철수",
            "phone": "02-9876-5432"
        },
        "item_list": [
            {
                "name": "A제품",
                "spec": "고급형",
                "quantity": 5,
                "unit_price": 100000
            },
            {
                "name": "B서비스",
                "spec": "프리미엄",
                "quantity": 1,
                "unit_price": 250000
            }
        ],
        "amount_summary": {
            "supply_sum": 750000,
            "vat_sum": 75000,
            "grand_total": 825000,
            "total_in_korean": "팔십이만오천원정"
        }
    }
    
    # 템플릿 렌더링
    template = env.get_template('transaction.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "거래명세서" in result
    assert data["metadata"]["document_number"] in result
    assert data["metadata"]["date_issued"] in result
    assert data["supplier_info"]["company_name"] in result
    assert data["customer_info"]["company_name"] in result
    assert str(data["amount_summary"]["grand_total"]) in result
    assert data["amount_summary"]["total_in_korean"] in result

def test_travel_application_template():
    """출장신청서 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "출장신청서",
        "metadata": {
            "document_number": "TA-2023-001",
            "date_issued": "2023-06-01"
        },
        "research_project_info": {
            "project_id": "PROJ-2023-005",
            "project_name": "인공지능 연구 프로젝트",
            "project_number": "AI-2023-005"
        },
        "travel_list": [
            {
                "employee_id": "EMP-001",
                "employee_name": "이영희",
                "purpose": "해외 학회 참석",
                "duration": "2023-06-15 ~ 2023-06-20",
                "destination": "미국 샌프란시스코"
            }
        ],
        "approval_list": [
            {
                "approver_id": "EMP-002",
                "approver_name": "김부장",
                "approval_date": "2023-06-02"
            }
        ]
    }
    
    # 템플릿 렌더링
    template = env.get_template('travel_application.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "출장신청서" in result
    assert data["metadata"]["document_number"] in result
    assert data["research_project_info"]["project_name"] in result
    assert data["travel_list"][0]["employee_name"] in result
    assert data["travel_list"][0]["purpose"] in result
    assert data["approval_list"][0]["approver_name"] in result

def test_travel_expense_template():
    """출장정산신청서 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "출장정산신청서",
        "metadata": {
            "document_number": "TE-2023-001",
            "date_issued": "2023-06-25",
            "reference_doc": "TA-2023-001"
        },
        "research_project_info": {
            "project_id": "PROJ-2023-005",
            "project_name": "인공지능 연구 프로젝트"
        },
        "traveler": {
            "employee_id": "EMP-001",
            "employee_name": "이영희",
            "department": "연구개발팀"
        },
        "expense_list": [
            {
                "date": "2023-06-15",
                "category": "교통비",
                "detail": "항공권",
                "amount": 1200000,
                "receipt": "영수증1.jpg"
            },
            {
                "date": "2023-06-15~20",
                "category": "숙박비",
                "detail": "호텔 5박",
                "amount": 800000,
                "receipt": "영수증2.jpg"
            }
        ],
        "amount_summary": {
            "advance_payment": 1500000,
            "total_expense": 2000000,
            "balance": -500000
        },
        "approval_list": [
            {
                "approver_id": "EMP-002",
                "approver_name": "김부장",
                "approval_date": "2023-06-26"
            }
        ]
    }
    
    # 템플릿 렌더링
    template = env.get_template('travel_expense.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "출장정산신청서" in result
    assert data["metadata"]["document_number"] in result
    assert data["traveler"]["employee_name"] in result
    assert str(data["amount_summary"]["total_expense"]) in result
    assert str(data["amount_summary"]["balance"]) in result

def test_meeting_expense_template():
    """회의비사용신청서 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "회의비사용신청서",
        "metadata": {
            "document_number": "ME-2023-001",
            "date_issued": "2023-07-05"
        },
        "research_project_info": {
            "project_id": "PROJ-2023-005",
            "project_name": "인공지능 연구 프로젝트"
        },
        "meeting_info": {
            "date": "2023-07-04 14:00~16:00",
            "place": "본사 회의실 3층",
            "purpose": "연구 진행상황 점검 및 향후 계획 논의",
            "participants": "이영희, 김철수, 박민지, 외부인사 2명"
        },
        "expense_info": {
            "expense_type": "식비",
            "amount": 150000,
            "payment_method": "법인카드"
        },
        "applicant_info": {
            "apply_date": "2023-07-05",
            "applicant_id": "EMP-001",
            "applicant_name": "이영희"
        },
        "approval_list": [
            {
                "approver_id": "EMP-002",
                "approver_name": "김부장",
                "approval_date": "2023-07-06"
            }
        ]
    }
    
    # 템플릿 렌더링
    template = env.get_template('meeting_expense.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "회의비사용신청서" in result
    assert data["metadata"]["document_number"] in result
    assert data["meeting_info"]["purpose"] in result
    assert data["meeting_info"]["participants"] in result
    assert str(data["expense_info"]["amount"]) in result
    assert data["expense_info"]["payment_method"] in result

def test_meeting_minutes_template():
    """회의록 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "회의록",
        "metadata": {
            "document_number": "MM-2023-001",
            "date_issued": "2023-07-05"
        },
        "research_project_info": {
            "project_id": "PROJ-2023-005",
            "project_name": "인공지능 연구 프로젝트"
        },
        "meeting_info": {
            "title": "7월 연구 진행상황 점검 회의",
            "date": "2023-07-04 14:00~16:00",
            "place": "본사 회의실 3층",
            "participants": "이영희(팀장), 김철수(연구원), 박민지(연구원), 외부인사 2명"
        },
        "meeting_content": {
            "agenda": "1. 전월 연구 성과 보고\n2. 문제점 및 해결 방안 논의\n3. 향후 연구 계획 수립",
            "discussion": "전월 연구에서 데이터 수집 과정의 문제점이 발견되었으며, 이를 해결하기 위한 방안으로...",
            "conclusion": "데이터 수집 방법을 개선하고, 8월까지 초기 모델을 개발하기로 결정함",
            "action_items": "1. 김철수: 데이터 수집 방법 개선 (7/15까지)\n2. 박민지: 초기 모델 설계 (7/30까지)"
        },
        "writer_info": {
            "name": "이영희",
            "position": "팀장",
            "department": "연구개발팀"
        }
    }
    
    # 템플릿 렌더링
    template = env.get_template('meeting_minutes.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "회의록" in result
    assert data["metadata"]["document_number"] in result
    assert data["meeting_info"]["title"] in result
    assert data["meeting_info"]["participants"] in result
    assert data["meeting_content"]["agenda"] in result
    assert data["meeting_content"]["conclusion"] in result
    assert data["writer_info"]["name"] in result

def test_purchase_request_template():
    """구매의뢰서 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "구매의뢰서",
        "metadata": {
            "document_number": "PR-2023-001",
            "date_issued": "2023-07-10"
        },
        "research_project_info": {
            "project_id": "PROJ-2023-005",
            "project_name": "인공지능 연구 프로젝트"
        },
        "purchase_reason": "연구 데이터 처리를 위한 컴퓨팅 장비 구입",
        "item_list": [
            {
                "name": "고성능 서버",
                "spec": "CPU: i9, RAM: 64GB, SSD: 2TB",
                "quantity": 2,
                "unit_price": 3000000,
                "amount": 6000000,
                "purpose": "데이터 처리 및 모델 학습용"
            },
            {
                "name": "GPU 카드",
                "spec": "NVIDIA RTX 4090",
                "quantity": 4,
                "unit_price": 2500000,
                "amount": 10000000,
                "purpose": "딥러닝 모델 학습용"
            }
        ],
        "amount_summary": {
            "supply_sum": 16000000,
            "vat_sum": 1600000,
            "grand_total": 17600000,
            "total_in_korean": "일천칠백육십만원정"
        },
        "applicant_info": {
            "apply_date": "2023-07-10",
            "applicant_id": "EMP-001",
            "applicant_name": "이영희"
        },
        "approval_list": [
            {
                "approver_id": "EMP-002",
                "approver_name": "김부장",
                "approval_date": "2023-07-11"
            }
        ]
    }
    
    # 템플릿 렌더링
    template = env.get_template('purchase_request.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "구매의뢰서" in result
    assert data["metadata"]["document_number"] in result
    assert data["purchase_reason"] in result
    assert data["item_list"][0]["name"] in result
    assert str(data["amount_summary"]["grand_total"]) in result
    assert data["amount_summary"]["total_in_korean"] in result

def test_expert_plan_template():
    """전문가활용계획서 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "전문가활용계획서",
        "metadata": {
            "document_number": "EP-2023-001",
            "date_issued": "2023-07-15"
        },
        "research_project_info": {
            "project_id": "PROJ-2023-005",
            "project_name": "인공지능 연구 프로젝트"
        },
        "expert_info": {
            "name": "박교수",
            "institution": "서울대학교",
            "position": "교수",
            "birth_date": "1970-05-15",
            "email": "professor@snu.ac.kr",
            "phone": "010-1234-5678",
            "address": "서울시 관악구 관악로 1",
            "bank_info": "국민은행",
            "account_number": "123-45-6789"
        },
        "util_plan": {
            "start_date": "2023-08-01",
            "end_date": "2023-08-31",
            "purpose": "인공지능 모델 설계 자문",
            "content": "연구 방향성 검토 및 알고리즘 설계 자문",
            "fee": 1000000
        },
        "approval_list": [
            {
                "approver_id": "EMP-002",
                "approver_name": "김부장",
                "approval_date": "2023-07-16"
            }
        ],
        "applicant_info": {
            "apply_date": "2023-07-15",
            "applicant_id": "EMP-001",
            "applicant_name": "이영희"
        }
    }
    
    # 템플릿 렌더링
    template = env.get_template('expert_plan.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "전문가활용계획서" in result
    assert data["metadata"]["document_number"] in result
    assert data["expert_info"]["name"] in result
    assert data["expert_info"]["institution"] in result
    assert data["util_plan"]["purpose"] in result
    assert str(data["util_plan"]["fee"]) in result
    assert data["applicant_info"]["applicant_name"] in result

def test_expert_confirm_template():
    """전문가자문확인서 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "전문가자문확인서",
        "metadata": {
            "document_number": "EC-2023-001",
            "date_issued": "2023-08-31"
        },
        "research_project_info": {
            "project_id": "PROJ-2023-005",
            "project_name": "인공지능 연구 프로젝트"
        },
        "expert_info": {
            "name": "박교수",
            "institution": "서울대학교",
            "position": "교수",
            "birth_date": "1970-05-15",
            "email": "professor@snu.ac.kr",
            "phone": "010-1234-5678",
            "address": "서울시 관악구 관악로 1",
            "bank_info": "국민은행",
            "account_number": "123-45-6789"
        },
        "consult_result": {
            "date": "2023-08-15",
            "place": "서울대학교 공과대학",
            "method": "대면 회의",
            "content": "인공지능 모델의 설계 방향에 대한 조언 및 검토 의견 제시\n데이터 처리 방법론에 대한 자문",
            "fee": 1000000
        },
        "applicant_info": {
            "apply_date": "2023-08-31",
            "applicant_id": "EMP-001",
            "applicant_name": "이영희",
            "stamp": "stamp.png"
        }
    }
    
    # 템플릿 렌더링
    template = env.get_template('expert_confirm.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "전문가자문확인서" in result
    assert data["metadata"]["document_number"] in result
    assert data["expert_info"]["name"] in result
    assert data["consult_result"]["method"] in result
    assert data["consult_result"]["content"] in result
    assert str(data["consult_result"]["fee"]) in result
    assert data["applicant_info"]["applicant_name"] in result

def test_expenditure_template():
    """지출결의서 템플릿 테스트"""
    # 더미 데이터 생성
    data = {
        "document_type": "지출결의서",
        "metadata": {
            "document_number": "EX-2023-001",
            "date_issued": "2023-09-05",
            "writer": "이영희",
            "department": "연구개발팀",
            "purpose": "연구 장비 구매 비용 지출"
        },
        "expense_list": [
            {
                "item_name": "서버 구매비",
                "amount": 6000000,
                "memo": "인보이스 #INV-001"
            },
            {
                "item_name": "GPU 카드 구매비",
                "amount": 10000000,
                "memo": "인보이스 #INV-002"
            }
        ],
        "amount_summary": {
            "supply_sum": 16000000,
            "vat_sum": 1600000,
            "grand_total": 17600000,
            "total_in_korean": "일천칠백육십만원정"
        },
        "applicant_info": {
            "apply_date": "2023-09-05",
            "applicant_id": "EMP-001",
            "applicant_name": "이영희"
        },
        "approval_list": [
            {
                "approver_id": "EMP-002",
                "approver_name": "김부장",
                "approval_date": "2023-09-06"
            },
            {
                "approver_id": "EMP-003",
                "approver_name": "박이사",
                "approval_date": "2023-09-07"
            }
        ]
    }
    
    # 템플릿 렌더링
    template = env.get_template('expenditure.html')
    result = template.render(data=data)
    
    # 기본 검증
    assert "지출결의서" in result
    assert data["metadata"]["document_number"] in result
    assert data["metadata"]["purpose"] in result
    assert data["expense_list"][0]["item_name"] in result
    assert str(data["amount_summary"]["grand_total"]) in result
    assert data["amount_summary"]["total_in_korean"] in result
    assert data["applicant_info"]["applicant_name"] in result
    assert data["approval_list"][0]["approver_name"] in result 