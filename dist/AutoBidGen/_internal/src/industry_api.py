"""
조달청 업종기반법령정보서비스 API 연동 모듈

업종코드를 사용하여 업종명, 근거법령을 조회합니다.
API: 업종기반법령정보서비스 (IndstrytyBaseLawrgltInfoService)
오퍼레이션: getIndstrytyBaseLawrgltInfoList
"""

import requests
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# 업종기반법령정보서비스 API URL
INDUSTRY_API_URL = "https://apis.data.go.kr/1230000/ao/IndstrytyBaseLawrgltInfoService/getIndstrytyBaseLawrgltInfoList"

# 고정 서비스키
G2B_SERVICE_KEY = "230e69c867401697f9bba247e69206e968535f31cc4d1f116110ff664c1106de"


def get_industry_info_from_api(industry_code: str) -> Optional[Dict[str, str]]:
    """
    조달청 업종기반법령정보서비스 API로 업종 정보 조회
    
    Args:
        industry_code: 업종코드
        
    Returns:
        Dict with keys: industry_name (업종명), law_basis (근거법령)
        None if not found
    """
    if not industry_code:
        return None
    
    try:
        # API 호출
        params = {
            "ServiceKey": G2B_SERVICE_KEY,
            "pageNo": 1,
            "numOfRows": 10,
            "indstrytyCd": industry_code,  # 업종분류코드
            "type": "json",
        }
        
        print(f"[Industry API] Calling: {INDUSTRY_API_URL}")
        print(f"[Industry API] Param: indstrytyCd={industry_code}")
        
        response = requests.get(INDUSTRY_API_URL, params=params, timeout=15)
        print(f"[Industry API] Response code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
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
                print(f"[INFO] No results for industry code: {industry_code}")
                return None
            
            # items가 리스트인 경우
            if isinstance(items, list):
                item_list = items
            elif isinstance(items, dict):
                item_list = [items]
            else:
                item_list = []
            
            # 첫 번째 결과에서 업종 정보 추출
            if item_list:
                first_item = item_list[0]
                
                # 업종명 (여러 필드에서 찾기)
                industry_name = (
                    first_item.get("indstrytyNm") or          # 업종명
                    ""
                )
                
                # 근거법령
                law_basis = (
                    first_item.get("baseLawordNm") or             # 기준법령명
                    ""
                )
                
                # 법령조항
                law_article = (
                    first_item.get("baseLawordArtclClauseNm") or  # 법령조항
                    first_item.get("lawArtcl") or                 # 폴백
                    ""
                )
                
                if industry_name:
                    result = {
                        "industry_name": industry_name,
                        "law_basis": law_basis,
                        "law_article": law_article,
                        "industry_code": industry_code
                    }
                    print(f"[OK] Industry API found: {industry_code} -> {industry_name}")
                    return result
            
            print(f"[INFO] No industry info found for: {industry_code}")
        
        elif response.status_code == 403:
            print(f"[ERROR] API 403: Need to apply for IndstrytyBaseLawrgltInfoService")
        else:
            print(f"[ERROR] API error ({response.status_code})")
        
        return None
        
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] Industry code: {industry_code}")
        return None
    except Exception as e:
        print(f"[ERROR] Industry code {industry_code}: {e}")
        return None


def get_industry_info(industry_code: str) -> Optional[Dict[str, str]]:
    """
    업종코드로 업종 정보 조회 (API + 폴백)
    """
    if not industry_code:
        return None
    
    # API 조회
    api_result = get_industry_info_from_api(industry_code)
    if api_result:
        return api_result
    
    # 폴백: 빈 값 반환 (사용자가 직접 입력하도록)
    return {
        "industry_name": "",
        "law_basis": "",
        "law_article": "",
        "industry_code": industry_code
    }


def get_industry_infos(industry_codes: List[str], max_workers: int = 3) -> Dict[str, Dict[str, str]]:
    """여러 업종코드의 업종 정보를 조회"""
    if not industry_codes:
        return {}
    
    results: Dict[str, Dict[str, str]] = {}
    unique_codes = list(set(industry_codes))
    
    print(f"[Industry API] Looking up {len(unique_codes)} industry codes...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_code = {
            executor.submit(get_industry_info, code): code 
            for code in unique_codes
        }
        
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try:
                results[code] = future.result()
            except Exception as e:
                print(f"[ERROR] {code} lookup failed: {e}")
                results[code] = {
                    "industry_name": f"업종 ({code})",
                    "law_basis": "",
                    "industry_code": code
                }
    
    success_count = sum(1 for v in results.values() if v and v.get("industry_name") and "(" not in v.get("industry_name", ""))
    print(f"[DONE] Industry lookup complete: {success_count}/{len(unique_codes)} from API")
    
    return results


if __name__ == "__main__":
    # 테스트
    test_codes = ["1234", "5678"]
    print("\n--- IndstrytyBaseLawrgltInfoService Test ---")
    results = get_industry_infos(test_codes)
    print("\nResults:")
    for code, info in sorted(results.items()):
        print(f"  {code}: {info}")
