"""애플리케이션 설정"""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """통합 설정 - 환경변수를 오버라이드 가능"""
    
    # AI 설정
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model_text: str = os.getenv("OPENAI_MODEL_TEXT", "gpt-4o")
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    
    # 나라장터 입찰공고정보서비스 (기존)
    G2B_BID_BASE_URL = os.getenv("G2B_BID_BASE_URL", "https://apis.data.go.kr/1230000/ad/BidPublicInfoService")
    # 조달청 물품목록정보서비스 (추가)
    G2B_THNG_BASE_URL = os.getenv("G2B_THNG_BASE_URL", "https://apis.data.go.kr/1230000/ao/ThngListInfoService/getThngPrdnmLocplcAccotListlnfolnfoPrdlstSearch")

    G2B_SERVICE_KEY = os.getenv("G2B_SERVICE_KEY", "230e69c867401697f9bba247e69206e968535f31cc4d1f116110ff664c1106de")  # 공공데이터포털 서비스키(Encoding/Decoding 주의)

    
    # LangSmith Tracing
    langchain_tracing_v2: str = os.getenv("LANGCHAIN_TRACING_V2", "true")
    langchain_endpoint: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    langchain_api_key: str | None = os.getenv("LANGCHAIN_API_KEY")
    langchain_project: str = os.getenv("LANGCHAIN_PROJECT", "Auto-Bid-Gen")
    
    # 저장소 경로
    data_dir: Path = Path(os.getenv("DATA_DIR", "./data")).resolve()
    cache_dir: Path = Path(os.getenv("CACHE_DIR", "./cache")).resolve()


def ensure_dirs(settings: Settings) -> None:
    """필요한 디렉토리 생성"""
    for d in [settings.data_dir, settings.cache_dir]:
        d.mkdir(parents=True, exist_ok=True)


# 전역 설정 인스턴스
settings = Settings()

# [Dynamic Configuration]
# 고시금액 (기본값: 2.3억원) - API 연동 실패 시 이 값이 사용됨
_LIMIT_GOSI: int = 230000000

def get_limit_gosi() -> int:
    """현재 설정된 기획재정부 고시금액을 반환합니다."""
    return _LIMIT_GOSI

def set_limit_gosi(amount: int) -> None:
    """고시금액을 업데이트합니다."""
    global _LIMIT_GOSI
    _LIMIT_GOSI = amount
    print(f"[Config] Updated LIMIT_GOSI: {amount:,}원")

def initialize_notice_amount() -> None:
    """
    서버 시작 시 고시금액을 비동기적으로(또는 동기적으로) 업데이트합니다.
    API 호출 실패 시 기본값을 유지합니다.
    """
    try:
        from src.utils.notice_fetcher import fetch_gosi_amount
        print("[Config] Initializing GOSI Amount...")
        
        # 외부 API 호출
        fetched_amount = fetch_gosi_amount()
        
        if fetched_amount:
            set_limit_gosi(fetched_amount)
        else:
            print(f"[Config] Using default LIMIT_GOSI: {get_limit_gosi():,}원")
            
    except Exception as e:
        print(f"[Config] Failed to initialize notice amount: {e}")
