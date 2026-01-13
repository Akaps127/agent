"""
조달청 물품목록정보서비스 API 연동 모듈

세부품명번호(10자리)를 사용하여 물품명을 조회합니다.
API: 조달청 물품목록정보서비스 (ThngListInfoService)
오퍼레이션: getThngPrdnmLocplcAccotListInfoInfoLocplcSearch
"""

import requests
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import settings

# 물품목록정보서비스 API URL
THNG_LIST_API_URL = "https://apis.data.go.kr/1230000/ao/ThngListInfoService/getThngPrdnmLocplcAccotListInfoInfoLocplcSearch"

# 고정 서비스키
G2B_SERVICE_KEY = "230e69c867401697f9bba247e69206e968535f31cc4d1f116110ff664c1106de"

# 대분류 코드 → 카테고리명 (폴백용)
MAJOR_CATEGORIES = {
    "40": "법률/금융/비즈니스서비스",
    "41": "정보통신장비",
    "42": "전자부품",
    "43": "사무용기기/소프트웨어",
    "44": "사무용가구", 
    "45": "의료장비",
    "46": "실험/연구장비",
    "47": "산업기계",
    "48": "차량/운송장비",
    "49": "건설자재",
    "50": "식품/농산물",
    "51": "의약품/화학물",
    "52": "의류/섬유",
    "53": "연료/에너지",
    "54": "건축/건설",
    "55": "보안장비",
    "56": "청소/위생용품",
    "70": "임대서비스",
    "80": "엔지니어링",
    "84": "교육/훈련",
    "25": "차량/교통수단",
}


def get_category_name(item_code: str) -> str:
    """대분류 코드에서 카테고리명 반환"""
    if len(item_code) >= 2:
        return MAJOR_CATEGORIES.get(item_code[:2], "일반물품")
    return "일반물품"


def get_product_name_from_api(item_code: str) -> Optional[str]:
    """
    조달청 물품목록정보서비스 API로 물품명 조회
    세부품명번호(10자리)로 검색하여 물품명 반환
    """
    if not item_code or len(item_code) != 10:
        return None
    
    try:
        # API 호출
        params = {
            "ServiceKey": G2B_SERVICE_KEY,
            "pageNo": 1,
            "numOfRows": 1,
            "dtilPrdctClsfcNo": item_code,  # 10자리 세부품명번호 (i 포함 주의)
            "type": "json",
        }
        
        print(f"[API] Calling: {THNG_LIST_API_URL}")
        print(f"[API] Param: dtlPrdctClsfcNo={item_code}")
        
        response = requests.get(THNG_LIST_API_URL, params=params, timeout=15)
        print(f"[API] Response code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"[API] Response data: {data}")
            except Exception as e:
                print(f"[WARN] JSON parse failed: {response.text[:200]}")
                return None
            
            # 응답 구조 파싱
            response_data = data.get("response", {})
            header = response_data.get("header", {})
            result_code = header.get("resultCode", "")
            
            if result_code != "00":
                print(f"[WARN] API result code: {result_code} - {header.get('resultMsg', '')}")
                return None
            
            body = response_data.get("body", {})
            items = body.get("items", [])
            
            if not items or items == "":
                print(f"[INFO] No results for: {item_code}")
                return None
            
            # items가 리스트인 경우
            if isinstance(items, list):
                item_list = items
            elif isinstance(items, dict):
                item_list = [items]
            else:
                item_list = []
            
            # 첫 번째 결과에서 물품명 추출 (dtlPrdctClsfcNo로 정확히 검색했으므로)
            if item_list:
                first_item = item_list[0]
                # 가능한 물품명 필드들 (우선순위: prdctClsfcNoNm 먼저)
                product_name = (
                    first_item.get("prdctClsfcNoNm") or  # 물품분류명 (수질분석기)
                    first_item.get("prdnm") or           # 품명
                    first_item.get("dtlPrdctClsfcNoNm") or  # 세부품명
                    first_item.get("dtilPrdctClsfcNoNm") or  # 세부품명 (다른 표기)
                    first_item.get("thngNm")             # 물품명
                )
                if product_name:
                    print(f"[OK] API found: {item_code} -> {product_name}")
                    return product_name
            
            print(f"[INFO] No product name found for: {item_code}")
        
        elif response.status_code == 403:
            print(f"[ERROR] API 403: Need to apply for ThngListInfoService")
        else:
            print(f"[ERROR] API error ({response.status_code})")
        
        return None
        
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] {item_code}")
        return None
    except Exception as e:
        print(f"[ERROR] {item_code}: {e}")
        return None


def get_product_name(item_code: str) -> Optional[str]:
    """
    세부품명번호로 물품명 조회 (우선순위)
    1. 조달청 물품목록정보서비스 API
    2. 카테고리 추론 (폴백)
    """
    if not item_code:
        return None
    
    if len(item_code) != 10:
        print(f"[WARN] Invalid item code format: {item_code}")
        return f"Product ({item_code})"
    
    # 1. API 조회 (최우선)
    api_name = get_product_name_from_api(item_code)
    if api_name:
        return api_name
    
    # 2. 카테고리 추론 (최종 폴백)
    category = get_category_name(item_code)
    print(f"[INFO] Fallback to category: {item_code} -> {category}")
    return f"{category} ({item_code})"


def get_product_names(item_codes: List[str], max_workers: int = 3) -> Dict[str, Optional[str]]:
    """여러 세부품명번호의 물품명을 조회"""
    if not item_codes:
        return {}
    
    results: Dict[str, Optional[str]] = {}
    unique_codes = list(set(item_codes))
    
    print(f"[API] Looking up {len(unique_codes)} item codes...")
    print(f"[API] Using: ThngListInfoService (API Only)")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_code = {
            executor.submit(get_product_name, code): code 
            for code in unique_codes
        }
        
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try:
                results[code] = future.result()
            except Exception as e:
                print(f"[ERROR] {code} lookup failed: {e}")
                results[code] = f"{get_category_name(code)} ({code})"
    
    success_count = sum(1 for v in results.values() if v and "(" not in v)
    print(f"[DONE] Lookup complete: {success_count}/{len(unique_codes)} from API")
    
    return results


if __name__ == "__main__":
    test_codes = ["4111331501", "4612220601", "2511152201"]
    print("\n--- ThngListInfoService Test (API Only) ---")
    results = get_product_names(test_codes)
    print("\nResults:")
    for code, name in sorted(results.items()):
        print(f"  {code}: {name}")
