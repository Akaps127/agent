from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from openai import OpenAI 
import uvicorn
import shutil
import os
import tempfile
import asyncio

# 모듈 임포트
from src.parser import parse_document
from src.nodes.planner import plan_notice
from src.nodes.writer import write_notice
from src.nodes.docx_writer import generate_docx
from src.schema import PurchasePlan, AuditReport
from src.config import initialize_notice_amount
from src.parameters import get_parameters_definition, ParameterRules
from src.services.verification_service import NoticeVerificationService

def get_user_api_key(authorization: str = Header(None)): 
    if not authorization: 
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    return authorization.replace("Bearer ", "").strip() 

def call_openai(user_api_key: str, messages: list): 
    client = OpenAI(api_key=user_api_key)
    res = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages=messages
    )
    return res.choices[0].message.content 

# 허용 파일 확장자
ALLOWED_EXTENSIONS = {".pdf", ".hwp"}

app = FastAPI(title="Auto-Bid-Gen API", description="AI-based Contract Notice Generator (2-Step)")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://agent-87pu9nxuv-akaps127s-projects.vercel.app",
        "https://agent-nu-brown.vercel.app",], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/auth/check")
async def auth_check(authorization: str = Header(None)):
    user_api_key = get_user_api_key(authorization) 
    try: 
        msg = call_openai(user_api_key, [{"role": "user", "content": "Say OK"}])
        return {"ok":True, "message": msg} 
    except Exception as e: 
        raise HTTPException(status_code=401, detail=f"Invalid API Key: {str(e)}")


@app.on_event("startup")
async def startup_event():
    # 고시금액 초기화 (외부 API 연동)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, initialize_notice_amount)

# [Debug] Global Exception Handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    error_msg = f"[ERROR] Global Error: {str(exc)}\n{traceback.format_exc()}"
    print(error_msg)
    with open("server_error.log", "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n{error_msg}\n")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()},
    )

# [Step 1] PDF/HWP에서 데이터만 뽑아내기
@app.post("/extract", response_model=PurchasePlan)
async def extract_data(file: UploadFile = File(...)):
    print(f"[Extract] Processing {file.filename}")
    
    # 파일 확장자 체크 (PDF, HWP 허용)
    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="PDF 또는 HWP 파일만 가능합니다.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Parser 실행 (PDF/HWP 자동 감지)
        # Run in thread pool to avoid blocking async event loop
        loop = asyncio.get_event_loop()
        extracted_data = await loop.run_in_executor(None, parse_document, tmp_path)
        
        # 디버그: 추출된 데이터 로깅
        print(f"[API Response] item_codes: {extracted_data.item_codes}")
        print(f"[API Response] item_names: {extracted_data.item_names}")
        
        return extracted_data
    except Exception as e:
        print(f"[ERROR] Parser Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# [Parameters API] 4대 파라미터 정의 제공
@app.get("/parameters")
async def get_parameters():
    """프론트엔드에서 사용할 4대 파라미터 정의를 반환합니다."""
    try:
        params = get_parameters_definition()
        return params.model_dump()
    except Exception as e:
        print(f"[ERROR] Parameters Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# [Parameters API] 선택 가능한 입찰방법 조회
class AvailableBiddingMethodsRequest(BaseModel):
    winner_determination: str

@app.post("/parameters/available_bidding_methods")
async def get_available_bidding_methods(req: AvailableBiddingMethodsRequest):
    """낙찰자결정방법에 따라 선택 가능한 입찰방법 목록을 반환합니다."""
    try:
        methods = ParameterRules.get_available_bidding_methods(req.winner_determination)
        return {"available_methods": methods}
    except Exception as e:
        print(f"[ERROR] Available Bidding Methods Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# [Parameters API] 선택 가능한 낙찰자결정방법 조회
class AvailableWinnerMethodsRequest(BaseModel):
    bidding_method: str

@app.post("/parameters/available_winner_methods")
async def get_available_winner_methods(req: AvailableWinnerMethodsRequest):
    """입찰방법에 따라 선택 가능한 낙찰자결정방법 목록을 반환합니다."""
    try:
        methods = ParameterRules.get_available_winner_methods(req.bidding_method)
        return {"available_methods": methods}
    except Exception as e:
        print(f"[ERROR] Available Winner Methods Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# [Parameters API] 파라미터 유효성 검사
class ValidateParametersRequest(BaseModel):
    winner_determination: str
    bidding_method: str

@app.post("/parameters/validate")
async def validate_parameters(req: ValidateParametersRequest):
    """입찰방법과 낙찰자결정방법의 조합이 유효한지 검사합니다."""
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

# [Step 2] 확정된 데이터로 공고문 만들기 (검증 포함)
class GenerateRequest(BaseModel):
    plan_data: PurchasePlan  # 사용자가 수정한 데이터
    enable_verification: bool = True  # 검증 활성화 여부

# Store generated files for download
GENERATED_FILES = {}

@app.post("/generate_from_data")
async def generate_from_data(req: GenerateRequest, authorization: str = Header(None)):
    user_api_key = get_user_api_key(authorization)
    print(f"[Generate] Creating notice for {req.plan_data.notice_name}")
    try:
        # Run synchronous nodes in thread pool
        loop = asyncio.get_event_loop()
        
        # 1. Planner 실행 (수정된 예산, 날짜 등을 바탕으로 전략 다시 수립)
        planned_notice = await loop.run_in_executor(None, plan_notice, req.plan_data)
        
        # 2. [NEW] 검증 실행 (공고문 생성 전에 수행)
        verification_report = None
        if req.enable_verification:
            print("[Generate] Running verification before generating notice...")
            service = NoticeVerificationService(api_key=user_api_key)
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
        
        # 3. Writer 실행 (HTML)
        final_html = await loop.run_in_executor(None, write_notice, req.plan_data, planned_notice)
        
        # 4. DOCX 생성
        from datetime import datetime
        docx_filename = f"notice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        docx_path = os.path.join(tempfile.gettempdir(), docx_filename)
        await loop.run_in_executor(None, generate_docx, req.plan_data, planned_notice, docx_path)
        
        # Store for download
        GENERATED_FILES[docx_filename] = docx_path
        print(f"[Generate] DOCX saved: {docx_path}")
        
        # 응답에 검증 결과 포함
        response = {
            "html_content": final_html,
            "planned_strategy": planned_notice.model_dump(),
            "docx_filename": docx_filename,  # Frontend can use this to download
        }
        
        # 검증 결과 추가
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
    """Download a generated DOCX file."""
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



# [NEW] 공고문 검증 API
class VerifyNoticeRequest(BaseModel):
    plan_data: PurchasePlan
    enable_legal_check: bool = True
    enable_peer_comparison: bool = True

@app.post("/verify_notice", response_model=AuditReport)
async def verify_notice(req: VerifyNoticeRequest, authorization: str = Header(None)):
    user_api_key = get_user_api_key(authorization)
    """
    공고문 검증 API
    
    - 규칙 기반 검증
    - AI 기반 법령 검증 (Claude/OpenAI)
    - 나라장터 유사 공고 비교
    
    Returns:
        AuditReport: 통합 검증 리포트
    """
    print(f"[Verify] Verifying notice: {req.plan_data.notice_name}")
    try:
        loop = asyncio.get_event_loop()
        
        # 검증 서비스 초기화 및 실행
        service = NoticeVerificationService(api_key=user_api_key)
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
