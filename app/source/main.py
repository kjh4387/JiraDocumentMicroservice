import os
import sys
from config.settings import get_settings
from config.di_container import DIContainer
from core.exceptions import DocumentAutomationError
from core.logging import get_logger
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = get_logger(__name__)

app = FastAPI()

def main():
    """메인 애플리케이션"""
    logger.info("Application starting")
    
    try:
        # 설정 로드
        config_path = os.environ.get("CONFIG_PATH")
        settings = get_settings(config_path)
        
        # PostgreSQL 포트 설정 확인
        if "port" not in settings.config["database"]:
            settings.config["database"]["port"] = int(os.environ.get("DB_PORT", 5432))
        
        # 의존성 주입 컨테이너 초기화
        container = DIContainer(settings.config)
        
        # 문서 서비스 가져오기
        document_service = container.document_service
        
        # 견적서 생성 예시
        estimate_data = {
            "document_type": "견적서",
            "metadata": {
                "document_number": "EST-2023-001",
                "date_issued": "2023-05-15",
                "receiver": "홍길동"
            },
            "supplier_info": {
                "company_id": "COMP-001"  # DB에서 회사 정보 조회
            },
            "item_list": [
                {
                    "name": "테스트 상품",
                    "quantity": 2,
                    "unit_price": 50000,
                    "amount": 100000,
                    "vat": 10000
                }
            ],
            "amount_summary": {
                "supply_sum": 100000,
                "vat_sum": 10000,
                "grand_total": 110000
            }
        }
        
        # 문서 생성
        result = document_service.create_document(estimate_data)
        
        # PDF 저장
        output_path = os.path.join(settings["output_dir"], "견적서.pdf")
        document_service.save_pdf(result['pdf'], output_path)
        logger.info("Estimate document created", output_path=output_path)
        
        # 출장신청서 생성 예시
        travel_data = {
            "document_type": "출장신청서",
            "research_project_info": {
                "project_id": "PROJ-001"  # DB에서 연구 과제 정보 조회
            },
            "travel_list": [
                {
                    "employee_id": "EMP-001",  # DB에서 직원 정보 조회
                    "purpose": "고객사 미팅",
                    "duration": "2023-06-01 ~ 2023-06-03",
                    "destination": "서울"
                }
            ],
            "metadata": {
                "document_number": "TRAVEL-2023-001",
                "date_issued": "2023-05-20"
            },
            "approval_list": [
                {
                    "employee_id": "EMP-002",  # DB에서 결재자 정보 조회
                    "approval_status": "대기"
                },
                {
                    "employee_id": "EMP-003",  # DB에서 결재자 정보 조회
                    "approval_status": "대기"
                }
            ]
        }
        
        # 문서 생성
        result = document_service.create_document(travel_data)
        
        # PDF 저장
        output_path = os.path.join(settings["output_dir"], "출장신청서.pdf")
        document_service.save_pdf(result['pdf'], output_path)
        logger.info("Travel application document created", output_path=output_path)
        
        logger.info("Application completed successfully")
        return 0
        
    except DocumentAutomationError as e:
        logger.error("Application error", error=str(e))
        return 1
    except Exception as e:
        logger.critical("Unexpected error", error=str(e), exc_info=True)
        return 2

@app.post("/api/documents")
async def create_document(request: DocumentRequestDTO):
    """문서 생성 API"""
    try:
        # DTO를 딕셔너리로 변환
        data = request.dict()
        
        # 문서 서비스 호출
        result = document_service.create_document(data)
        
        # 응답 변환 및 반환
        response = DocumentResponseDTO(
            document_id=result["document_id"],
            document_type=result["document_type"],
            created_at=result["created_at"],
            html=result.get("html"),
            pdf_url=f"/api/documents/{result['document_id']}/pdf"
        )
        
        return response
        
    except ValidationError as e:
        # 400 Bad Request - 유효하지 않은 요청
        error_detail = str(e)
        logger.warning("Validation error", error=error_detail)
        raise HTTPException(
            status_code=400,
            detail={"message": "유효하지 않은 문서 요청", "error": error_detail}
        )
        
    except RenderingError as e:
        # 422 Unprocessable Entity - 유효한 요청이지만 처리할 수 없음
        error_detail = str(e)
        logger.error("Rendering error", error=error_detail)
        raise HTTPException(
            status_code=422,
            detail={"message": "문서 렌더링 실패", "error": error_detail}
        )
        
    except DocumentAutomationError as e:
        # 500 Internal Server Error - 서버 오류
        error_detail = str(e)
        logger.error("Document automation error", error=error_detail)
        raise HTTPException(
            status_code=500,
            detail={"message": "문서 생성 실패", "error": error_detail}
        )

if __name__ == "__main__":
    sys.exit(main())
