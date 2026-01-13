
import re
import requests
import xml.etree.ElementTree as ET
from typing import Optional

# 기본 설정
LAW_API_BASE_URL = "https://www.law.go.kr/DRF"
DEFAULT_OC_ID = "leejayy4"  # 사용자가 제공한 OC ID

def fetch_gosi_amount(oc_id: str = DEFAULT_OC_ID) -> Optional[int]:
    """
    법제처 API를 통해 '기획재정부장관이 정하는 고시금액'을 검색하고,
    '물품' 관련 고시금액을 추출하여 반환합니다.
    
    Returns:
        추출된 금액(int) 또는 실패 시 None
    """
    try:
        # 1. 검색 API 호출 (행정규칙 검색)
        # target=admrul (행정규칙)
        search_url = f"{LAW_API_BASE_URL}/lawSearch.do"
        params = {
            "OC": oc_id,
            "target": "admrul",
            "type": "XML",
            "query": "국가계약법 고시금액"  # 더 간단한 검색어
        }
        
        print(f"[NoticeFetcher] Searching: {params['query']}")
        print(f"[NoticeFetcher] URL: {search_url}")
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"[NoticeFetcher] Search failed: {response.status_code}")
            return None
            
        # XML 파싱
        root = ET.fromstring(response.content)
        
        # 첫 번째 검색 결과의 일련번호(MST) 추출
        # 구조: <LawSearch> <law> <MST>123456</MST> ... </law> </LawSearch>
        # 정확도를 위해 '국가를 당사자로 하는 계약에 관한 법률' 관련성 확인이 좋으나,
        # 일단 가장 최신(상위) 결과를 사용
        first_law = root.find(".//law")
        if first_law is None:
            print("[NoticeFetcher] No search results found.")
            return None
            
        mst_seq = first_law.findtext("MST")
        doc_title = first_law.findtext("법령명") or first_law.findtext("행정규칙명")
        print(f"[NoticeFetcher] Found document: {doc_title} (MST: {mst_seq})")
        
        if not mst_seq:
            return None
            
        # 2. 상세 조회 API 호출
        detail_url = f"{LAW_API_BASE_URL}/lawService.do"
        detail_params = {
            "OC": oc_id,
            "target": "admrul",
            "type": "XML",
            "MST": mst_seq
        }
        
        detail_resp = requests.get(detail_url, params=detail_params, timeout=10)
        if detail_resp.status_code != 200:
            return None
            
        detail_root = ET.fromstring(detail_resp.content)
        
        # 본문 텍스트 추출 (조문 내용 등)
        # XML 구조는 복잡할 수 있으므로 전체 텍스트에서 검색
        # 다만, 'Jo' (조) 태그 등을 순회하는 것이 안전
        full_text = ""
        for content in detail_root.iter():
            if content.text:
                full_text += content.text + "\n"
                
        # 3. 금액 추출 정규식
        # 목표: "물품 ... 2억 3천만원" 등의 패턴
        # 예시: "물품의 제조ㆍ구매 및 용역의 경우에는 2억 1천만원"
        # 2024년 기준 2.2억, 2.3억 등 변동 가능.
        
        # 1차 시도: "물품" 주변의 "X억 X천만원" 찾기
        # Pattern: 물품...(약간의 거리)... (\d+)억\s*(\d+)?(천)?만원
        
        # 텍스트를 줄 단위로 보고 '물품'이 있는 줄에서 금액을 찾는 것이 안전
        lines = full_text.splitlines()
        candidate_amounts = []
        
        for line in lines:
            if "물품" in line and "경우" in line:
                # 2억 3천만원, 2억1천만원, 2억, 3억 등
                # (\d+)억 -> Group 1
                # (\s*(\d+)천)? -> Group 2 (optional)
                matches = re.findall(r'(\d+)억\s*(?:(\d+)천)?만원', line)
                if matches:
                    for m in matches:
                        억 = int(m[0])
                        천 = int(m[1]) if m[1] else 0
                        amount = (억 * 100000000) + (천 * 10000000)
                        candidate_amounts.append(amount)
                        print(f"[NoticeFetcher] Found amount candidate: {amount:,}원 in line: {line.strip()[:50]}...")

        if candidate_amounts:
            # 여러 개가 나올 수 있음 (건설, 물품, 용역 등).
            # 보통 물품/용역 금액은 동일하며 건설공사 금액(더 큼)과 다름.
            # 가장 빈도수가 높은 것 또는 가장 작은 것? 
            # 국가계약법 고시금액상: 공사 > 물품/용역. 
            # 물품 금액을 원하므로, 발견된 금액 중 '작은 쪽'일 가능성이 높음 (공사가 70~80억 수준)
            # 그러나 2.3억 주변이어야 함. 
            
            # Simple heuristic: 1억 ~ 10억 사이의 값 선택
            valid_amounts = [a for a in candidate_amounts if 100000000 <= a <= 1000000000]
            if valid_amounts:
                # 가장 자주 나오는 값 or 첫번째
                final_amount = valid_amounts[0]
                print(f"[NoticeFetcher] Decided amount: {final_amount:,}원")
                return final_amount
        
        print("[NoticeFetcher] Failed to extract valid amount pattern.")
        return None
        
    except Exception as e:
        print(f"[NoticeFetcher] Error: {e}")
        return None

if __name__ == "__main__":
    # Test execution
    amt = fetch_gosi_amount()
    print(f"Result: {amt}")
