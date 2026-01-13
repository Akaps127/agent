# -*- coding: utf-8 -*-
"""
AutoBidGen Standalone Application
백엔드 + 프론트엔드 통합 실행 파일
"""

import os
import sys
import webbrowser
import threading
import time

# PyInstaller 환경에서 리소스 경로 처리
def get_resource_path(relative_path):
    """PyInstaller로 패키징된 경우와 개발 환경 모두에서 리소스 경로를 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 경우
        base_path = sys._MEIPASS
    else:
        # 개발 환경
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# 환경 변수 설정 (패키징 환경에서 .env 파일 로드)
def setup_environment():
    """환경 변수 설정"""
    from dotenv import load_dotenv
    
    # .env 파일 로드 시도
    env_path = get_resource_path('.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"[Init] Loaded environment from: {env_path}")
    else:
        # 실행 파일 옆에 있는 .env 파일 확인
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        local_env = os.path.join(exe_dir, '.env')
        if os.path.exists(local_env):
            load_dotenv(local_env)
            print(f"[Init] Loaded environment from: {local_env}")
        else:
            print("[Warning] .env file not found. Please ensure API keys are set.")

# FastAPI 앱 설정
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import shutil
import tempfile
import asyncio

# 환경 설정
setup_environment()

# 모듈 임포트
from src.parser import parse_document
from src.nodes.planner import plan_notice
from src.nodes.writer import write_notice
from src.nodes.docx_writer import generate_docx
from src.schema import PurchasePlan, AuditReport
from src.config import initialize_notice_amount
from src.parameters import get_parameters_definition, ParameterRules
from src.services.verification_service import NoticeVerificationService

# 허용 파일 확장자
ALLOWED_EXTENSIONS = {".pdf", ".hwp"}

app = FastAPI(title="Auto-Bid-Gen", description="AI-based Contract Notice Generator")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 경로 설정 (프론트엔드)
FRONTEND_PATH = get_resource_path('frontend_static')

@app.on_event("startup")
async def startup_event():
    # 고시금액 초기화 (외부 API 연동)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, initialize_notice_amount)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    error_msg = f"[ERROR] Global Error: {str(exc)}\n{traceback.format_exc()}"
    print(error_msg)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()},
    )

# [Step 1] PDF/HWP에서 데이터만 뽑아내기
@app.post("/extract", response_model=PurchasePlan)
async def extract_data(file: UploadFile = File(...)):
    print(f"[Extract] Processing {file.filename}")
    
    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="PDF 또는 HWP 파일만 가능합니다.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        loop = asyncio.get_event_loop()
        extracted_data = await loop.run_in_executor(None, parse_document, tmp_path)
        print(f"[API Response] item_codes: {extracted_data.item_codes}")
        print(f"[API Response] item_names: {extracted_data.item_names}")
        return extracted_data
    except Exception as e:
        print(f"[ERROR] Parser Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# [Parameters API]
@app.get("/parameters")
async def get_parameters():
    try:
        params = get_parameters_definition()
        return params.model_dump()
    except Exception as e:
        print(f"[ERROR] Parameters Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class AvailableBiddingMethodsRequest(BaseModel):
    winner_determination: str

@app.post("/parameters/available_bidding_methods")
async def get_available_bidding_methods(req: AvailableBiddingMethodsRequest):
    try:
        methods = ParameterRules.get_available_bidding_methods(req.winner_determination)
        return {"available_methods": methods}
    except Exception as e:
        print(f"[ERROR] Available Bidding Methods Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class AvailableWinnerMethodsRequest(BaseModel):
    bidding_method: str

@app.post("/parameters/available_winner_methods")
async def get_available_winner_methods(req: AvailableWinnerMethodsRequest):
    try:
        methods = ParameterRules.get_available_winner_methods(req.bidding_method)
        return {"available_methods": methods}
    except Exception as e:
        print(f"[ERROR] Available Winner Methods Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ValidateParametersRequest(BaseModel):
    winner_determination: str
    bidding_method: str

@app.post("/parameters/validate")
async def validate_parameters(req: ValidateParametersRequest):
    try:
        is_valid, error_msg = ParameterRules.validate_bidding_method(
            req.winner_determination,
            req.bidding_method
        )
        return {
            "is_valid": is_valid,
            "error_message": error_msg if not is_valid else None
        }
    except Exception as e:
        print(f"[ERROR] Validate Parameters Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# [Step 2] 공고문 생성
class GenerateRequest(BaseModel):
    plan_data: PurchasePlan
    enable_verification: bool = True

GENERATED_FILES = {}

@app.post("/generate_from_data")
async def generate_from_data(req: GenerateRequest):
    print(f"[Generate] Creating notice for {req.plan_data.notice_name}")
    try:
        loop = asyncio.get_event_loop()
        
        planned_notice = await loop.run_in_executor(None, plan_notice, req.plan_data)
        
        verification_report = None
        if req.enable_verification:
            print("[Generate] Running verification before generating notice...")
            service = NoticeVerificationService()
            verification_report = await loop.run_in_executor(
                None,
                lambda: service.verify_notice(
                    req.plan_data,
                    notice=planned_notice,
                    enable_legal_check=True,
                    enable_peer_comparison=True
                )
            )
            print(f"[Generate] Verification complete. Risk level: {verification_report.overall_risk}")
        
        final_html = await loop.run_in_executor(None, write_notice, req.plan_data, planned_notice)
        
        from datetime import datetime
        docx_filename = f"notice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        docx_path = os.path.join(tempfile.gettempdir(), docx_filename)
        await loop.run_in_executor(None, generate_docx, req.plan_data, planned_notice, docx_path)
        
        GENERATED_FILES[docx_filename] = docx_path
        print(f"[Generate] DOCX saved: {docx_path}")
        
        response = {
            "html_content": final_html,
            "planned_strategy": planned_notice.model_dump(),
            "docx_filename": docx_filename,
        }
        
        if verification_report:
            response["verification"] = {
                "overall_risk": verification_report.overall_risk,
                "rule_violations": verification_report.rule_violations,
                "legal_findings": [f.model_dump() for f in verification_report.legal_findings],
                "benchmark_stats": [s.model_dump() for s in verification_report.benchmark_stats],
            }
        
        return response
    except Exception as e:
        print(f"[ERROR] Generate Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_docx/{filename}")
async def download_docx(filename: str):
    if filename not in GENERATED_FILES:
        raise HTTPException(status_code=404, detail="File not found or expired")
    
    file_path = GENERATED_FILES[filename]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

class VerifyNoticeRequest(BaseModel):
    plan_data: PurchasePlan
    enable_legal_check: bool = True
    enable_peer_comparison: bool = True

@app.post("/verify_notice", response_model=AuditReport)
async def verify_notice(req: VerifyNoticeRequest):
    print(f"[Verify] Verifying notice: {req.plan_data.notice_name}")
    try:
        loop = asyncio.get_event_loop()
        
        service = NoticeVerificationService()
        report = await loop.run_in_executor(
            None,
            lambda: service.verify_notice(
                req.plan_data,
                enable_legal_check=req.enable_legal_check,
                enable_peer_comparison=req.enable_peer_comparison
            )
        )
        
        return report
    except Exception as e:
        print(f"[ERROR] Verify Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# 정적 파일 서빙 (프론트엔드)
if os.path.exists(FRONTEND_PATH):
    app.mount("/", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")

def open_browser():
    """서버 시작 후 브라우저 열기"""
    time.sleep(2)  # 서버 초기화 대기
    webbrowser.open("http://localhost:8000")
    print("\n" + "="*50)
    print("  AutoBidGen이 시작되었습니다!")
    print("  브라우저에서 http://localhost:8000 을 열어주세요.")
    print("  종료하려면 이 창을 닫으세요.")
    print("="*50 + "\n")

def main():
    """메인 실행 함수"""
    print("\n" + "="*50)
    print("  AutoBidGen 시작 중...")
    print("="*50 + "\n")
    
    # 브라우저 자동 열기 (별도 스레드)
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # 서버 실행
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
