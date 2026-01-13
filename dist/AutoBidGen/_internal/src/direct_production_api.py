"""
중소기업 직접생산확인증명서 API 모듈

세부품명번호를 사용하여 해당 품목이 직접생산확인 대상인지 조회합니다.
API: 중소벤처기업부_직접생산확인증명서발급현황
"""

import requests
from typing import List, Dict, Optional

# API URL (공공데이터포털)
DIRECT_PROD_API_URL = "https://api.odcloud.kr/api/3061008/v1/uddi:f50783ce-1e73-4443-95a5-adbda8cc7e21"

# 서비스키
SERVICE_KEY = "230e69c867401697f9bba247e69206e968535f31cc4d1f116110ff664c1106de"


def check_direct_production_item(product_name: str) -> bool:
    """
    물품명(세부품명)이 직접생산확인 대상인지 확인
    API에서 세부품명이 존재하면 True 반환
    """
    if not product_name:
        return False
    
    try:
        params = {
            "serviceKey": SERVICE_KEY,
            "page": 1,
            "perPage": 10,
            "cond[세부품목::LIKE]": product_name,
            "returnType": "JSON"
        }
        
        print(f"[DirectProd API] Checking: {product_name}")
        response = requests.get(DIRECT_PROD_API_URL, params=params, timeout=10)
        print(f"[DirectProd API] Response code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total_count = data.get("totalCount", 0)
            
            if total_count > 0:
                print(f"[DirectProd API] Found {total_count} records for: {product_name}")
                return True
            else:
                print(f"[DirectProd API] No records for: {product_name}")
                return False
        else:
            print(f"[DirectProd API] Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[DirectProd API] Exception: {e}")
        return False


def get_direct_production_clause(item_code: str, product_name: str) -> Optional[str]:
    """
    직접생산확인증명서 조항 생성
    해당 품목이 직접생산확인 대상이면 조항 문구 반환
    """
    if check_direct_production_item(product_name):
        clause = (
            f"※ 중소기업제품 구매촉진 및 판로지원에 관한법률 제9조 및 동법 시행규칙 제5조 규정에 의한 "
            f"직접생산확인증명서[세부품명번호: {product_name}({item_code})]"
            f"(개찰일 전일까지 발급된 것으로 유효기간 내에 있어야 함)를 소지한 자"
        )
        return clause
    return None


def get_direct_production_clauses(item_codes: List[str], item_names: List[str]) -> List[str]:
    """
    여러 품목에 대한 직접생산확인증명서 조항 목록 생성
    """
    clauses = []
    
    for code, name in zip(item_codes, item_names):
        clause = get_direct_production_clause(code, name)
        if clause:
            clauses.append(clause)
    
    return clauses


if __name__ == "__main__":
    # 테스트
    test_items = [
        ("4411200201", "달력"),
        ("4111331501", "컴퓨터"),
    ]
    
    print("\n--- Direct Production Certificate API Test ---")
    for code, name in test_items:
        result = check_direct_production_item(name)
        print(f"  {name} ({code}): {'대상' if result else '비대상'}")
