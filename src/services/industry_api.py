"""
업종코드 API 서비스
공공데이터포털 업종코드 법령정보 조회 API 클라이언트
"""
import httpx
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

# API Configuration
API_KEY = "230e69c867401697f9bba247e69206e968535f31cc4d1f116110ff664c1106de"
BASE_URL = "http://apis.data.go.kr/1230000/IndstrytyInformationService/getIndstrytyBaseLawrgltInfoList"

# Cache for industry names to reduce API calls
_industry_cache: Dict[str, str] = {}

logger = logging.getLogger(__name__)


async def fetch_industry_name(industry_code: str) -> Optional[str]:
    """
    업종코드(4자리)로 업종명을 조회합니다.
    
    Args:
        industry_code: 4자리 업종코드 (예: "4608")
    
    Returns:
        업종명 문자열 또는 None (조회 실패 시)
    """
    # Check cache first
    if industry_code in _industry_cache:
        logger.info(f"Cache hit for industry code: {industry_code}")
        return _industry_cache[industry_code]
    
    try:
        params = {
            "serviceKey": API_KEY,
            "numOfRows": "10",
            "pageNo": "1",
            "inqryDiv": "1",  # 조회구분 (1: 업종코드)
            "inqryBgnDt": "",
            "inqryEndDt": "",
            "indstrytyCd": industry_code,  # 업종코드
            "type": "json"
        }
        
        logger.info(f"Fetching industry name for code: {industry_code}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response - structure may vary based on actual API
            # Common patterns: response.body.items.item[0].indstrytyNm
            if "response" in data:
                body = data.get("response", {}).get("body", {})
                items = body.get("items", {})
                
                if items:
                    item_list = items.get("item", [])
                    if isinstance(item_list, list) and len(item_list) > 0:
                        industry_name = item_list[0].get("indstrytyNm", None)
                    elif isinstance(item_list, dict):
                        industry_name = item_list.get("indstrytyNm", None)
                    else:
                        industry_name = None
                    
                    if industry_name:
                        _industry_cache[industry_code] = industry_name
                        logger.info(f"Found industry name: {industry_name} for code: {industry_code}")
                        return industry_name
            
            logger.warning(f"No industry name found for code: {industry_code}")
            return None
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching industry name: {e}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error fetching industry name: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching industry name: {e}")
        return None


async def fetch_multiple_industry_names(codes: list[str]) -> Dict[str, Optional[str]]:
    """
    여러 업종코드의 업종명을 한번에 조회합니다.
    
    Args:
        codes: 업종코드 리스트
    
    Returns:
        {업종코드: 업종명} 딕셔너리
    """
    results = {}
    for code in codes:
        if code and len(code) == 4:  # 4자리 코드만 처리
            results[code] = await fetch_industry_name(code)
    return results


def clear_cache():
    """캐시 초기화"""
    _industry_cache.clear()
    logger.info("Industry cache cleared")
