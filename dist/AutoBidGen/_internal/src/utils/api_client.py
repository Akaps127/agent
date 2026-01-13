import requests
from typing import Optional, Dict

class ContractInfoAPI:
    """
    Public Data Portal API Client for Contract Information.
    Uses 'Intelligent Mapping' (Mock) for Hackathon speed, falls back to API structure.
    """
    def __init__(self, api_key: str = "230e69c867401697f9bba247e69206e968535f31cc4d1f116110ff664c1106de"):
        self.api_key = api_key
        self.base_url = "http://apis.data.go.kr/1230000/BidPublicInfoService04" # Fake URL for structure
        
        # [Hackathon Fast-Track] Intelligent Mapping Table
        # Frequently used codes are cached for instant response
        self.MOCK_DB: Dict[str, str] = {
            "3592": "엔지니어링산업진흥법 제21조에 의한 엔지니어링사업(대기관리)",
            "7465": "대기환경보전법 제32조의2에 의한 대기오염측정기기관리대행업",
            "4608": "고압가스 안전관리법 제4조에 의한 고압가스판매업",
            "1234": "소프트웨어 진흥법 제24조에 의한 소프트웨어사업자(컴퓨터관련서비스사업)",
            # Add more as needed
        }

    def get_industry_qualification(self, code: str) -> str:
        """
        Returns the full legal qualification text for a given industry code.
        """
        # 1. Check Mock DB first (Fast Response)
        if code in self.MOCK_DB:
            return f"{self.MOCK_DB[code]} (업종코드: {code})"
        
        # 2. API Call (Simulation)
        # In a real scenario, we would call the API here.
        # response = requests.get(...)
        
        # 3. Fallback
        return f"관련 법령에 따른 업종코드 {code}를 등록한 자"
