"""
나라장터 유사공고 비교 검증 모듈
- AI 기반 유사 공고 시뮬레이션 (현재)
- 향후 실제 나라장터 API 연동 예정
"""

import os
import json
from typing import List, Dict, Any, Optional
from src.schema import PurchasePlan, PlannedNotice, BenchmarkStat

# AI 클라이언트
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# 유사 공고 생성 프롬프트
PEER_SEARCH_PROMPT = """당신은 나라장터 공고 데이터 전문가입니다. 아래 구매계획서와 유사한 공고 5건을 시뮬레이션하세요.

## 구매계획서 정보
- 공고명: {notice_name}
- 추정가격: {budget_supply:,}원
- 물품: {item_names}
- 계약방법: {contract_method}

## 응답 형식 (JSON)
유사한 공고 5건을 JSON 배열로 응답하세요:
```json
[
  {{
    "notice_id": "공고번호 (예: 2024-001-123456)",
    "notice_name": "공고명",
    "budget": 예산액(숫자),
    "joint_allowed": 공동계약허용여부(true/false),
    "has_region_limit": 지역제한여부(true/false),
    "has_sme_limit": 중소기업제한여부(true/false),
    "contract_method": "계약방법",
    "agency": "발주기관명"
  }}
]
```

JSON 배열만 응답하세요.
"""


def search_similar_notices_with_llm(
    plan: PurchasePlan,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    AI를 사용하여 유사 공고 데이터를 생성합니다 (시뮬레이션).
    
    Args:
        plan: 구매계획서
        api_key: AI API 키
    
    Returns:
        List[Dict]: 유사 공고 정보 리스트
    """
    prompt = PEER_SEARCH_PROMPT.format(
        notice_name=plan.notice_name,
        budget_supply=plan.budget_supply,
        item_names=", ".join(plan.item_names) if plan.item_names else "물품",
        contract_method=plan.contract_method_text
    )
    
    anthropic_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    response_text = None
    
    # Claude 호출
    if ANTHROPIC_AVAILABLE and anthropic_key:
        try:
            client = anthropic.Anthropic(api_key=anthropic_key)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
            print("[Peer Comparison] Claude 응답 수신 완료")
        except Exception as e:
            print(f"[Peer Comparison] Claude 호출 실패: {e}")
    
    # OpenAI Fallback
    if response_text is None and OPENAI_AVAILABLE and openai_key:
        try:
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500
            )
            response_text = response.choices[0].message.content
            print("[Peer Comparison] OpenAI 응답 수신 완료")
        except Exception as e:
            print(f"[Peer Comparison] OpenAI 호출 실패: {e}")
    
    # AI 응답 파싱
    if response_text:
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"[Peer Comparison] JSON 파싱 실패: {e}")
    
    # Fallback: 더미 데이터 생성
    return generate_mock_peers(plan)


def generate_mock_peers(plan: PurchasePlan) -> List[Dict[str, Any]]:
    """
    더미 유사 공고 데이터를 생성합니다.
    
    Args:
        plan: 구매계획서
    
    Returns:
        List[Dict]: 더미 유사 공고 리스트
    """
    budget = plan.budget_supply
    is_small = budget <= 100_000_000
    
    return [
        {
            "notice_id": "2024-001-000001",
            "notice_name": f"{plan.item_names[0] if plan.item_names else '물품'} 구매 (유사1)",
            "budget": int(budget * 0.9),
            "joint_allowed": False,
            "has_region_limit": False,
            "has_sme_limit": True,
            "contract_method": "소액수의" if is_small else "적격심사",
            "agency": "한국환경공단"
        },
        {
            "notice_id": "2024-001-000002",
            "notice_name": f"{plan.item_names[0] if plan.item_names else '물품'} 구매 (유사2)",
            "budget": int(budget * 1.1),
            "joint_allowed": False,
            "has_region_limit": False,
            "has_sme_limit": True,
            "contract_method": "소액수의" if is_small else "적격심사",
            "agency": "국립환경과학원"
        },
        {
            "notice_id": "2024-001-000003",
            "notice_name": f"{plan.item_names[0] if plan.item_names else '물품'} 구매 (유사3)",
            "budget": int(budget * 0.95),
            "joint_allowed": True,
            "has_region_limit": True,
            "has_sme_limit": True,
            "contract_method": "제한경쟁",
            "agency": "환경부"
        },
        {
            "notice_id": "2024-001-000004",
            "notice_name": f"{plan.item_names[0] if plan.item_names else '물품'} 구매 (유사4)",
            "budget": int(budget * 1.05),
            "joint_allowed": False,
            "has_region_limit": False,
            "has_sme_limit": True,
            "contract_method": "소액수의" if is_small else "적격심사",
            "agency": "한국수자원공사"
        },
        {
            "notice_id": "2024-001-000005",
            "notice_name": f"{plan.item_names[0] if plan.item_names else '물품'} 구매 (유사5)",
            "budget": int(budget * 0.85),
            "joint_allowed": False,
            "has_region_limit": False,
            "has_sme_limit": True,
            "contract_method": "소액수의" if is_small else "적격심사",
            "agency": "국립생태원"
        }
    ]


def compare_with_peers(
    notice: PlannedNotice,
    plan: PurchasePlan,
    peers: List[Dict[str, Any]]
) -> List[BenchmarkStat]:
    """
    유사 공고와 비교하여 벤치마크 통계를 생성합니다.
    
    Args:
        notice: 생성된 공고 전략
        plan: 구매계획서
        peers: 유사 공고 리스트
    
    Returns:
        List[BenchmarkStat]: 벤치마크 통계 리스트
    """
    stats = []
    
    if not peers:
        return stats
    
    # 1. 공동계약 비교
    your_joint = "허용" if plan.joint_venture_allow else "불허"
    peer_joint_count = sum(1 for p in peers if p.get("joint_allowed", False))
    peer_joint_pct = (peer_joint_count / len(peers)) * 100
    
    is_joint_outlier = (plan.joint_venture_allow and peer_joint_pct < 30) or \
                       (not plan.joint_venture_allow and peer_joint_pct > 70)
    
    stats.append(BenchmarkStat(
        field="공동계약",
        your_value=your_joint,
        peer_summary=f"유사공고 {len(peers)}건 중 {peer_joint_count}건({peer_joint_pct:.0f}%) 허용",
        outlier=is_joint_outlier,
        evidence_notice_ids=[p["notice_id"] for p in peers if p.get("joint_allowed", False)]
    ))
    
    # 2. 지역제한 비교
    your_region = "있음" if plan.region_restriction_text else "없음"
    peer_region_count = sum(1 for p in peers if p.get("has_region_limit", False))
    peer_region_pct = (peer_region_count / len(peers)) * 100
    
    is_region_outlier = (plan.region_restriction_text and peer_region_pct < 30) or \
                        (not plan.region_restriction_text and peer_region_pct > 70)
    
    stats.append(BenchmarkStat(
        field="지역제한",
        your_value=your_region,
        peer_summary=f"유사공고 {len(peers)}건 중 {peer_region_count}건({peer_region_pct:.0f}%) 제한",
        outlier=is_region_outlier,
        evidence_notice_ids=[p["notice_id"] for p in peers if p.get("has_region_limit", False)]
    ))
    
    # 3. 중소기업 제한 비교
    your_sme = "있음" if "중소기업" in (notice.sme_restriction or "") or "소기업" in (notice.sme_restriction or "") else "없음"
    peer_sme_count = sum(1 for p in peers if p.get("has_sme_limit", False))
    peer_sme_pct = (peer_sme_count / len(peers)) * 100
    
    is_sme_outlier = (your_sme == "없음" and peer_sme_pct > 50)
    
    stats.append(BenchmarkStat(
        field="중소기업제한",
        your_value=your_sme,
        peer_summary=f"유사공고 {len(peers)}건 중 {peer_sme_count}건({peer_sme_pct:.0f}%) 제한",
        outlier=is_sme_outlier,
        evidence_notice_ids=[p["notice_id"] for p in peers if p.get("has_sme_limit", False)]
    ))
    
    # 4. 예산 비교
    if peers:
        peer_budgets = [p.get("budget", 0) for p in peers if p.get("budget")]
        if peer_budgets:
            avg_budget = sum(peer_budgets) / len(peer_budgets)
            your_budget = plan.budget_supply
            
            # 평균의 ±30%를 벗어나면 이례적
            is_budget_outlier = your_budget < avg_budget * 0.7 or your_budget > avg_budget * 1.3
            
            stats.append(BenchmarkStat(
                field="예산규모",
                your_value=f"{your_budget:,}원",
                peer_summary=f"유사공고 평균 {avg_budget:,.0f}원 (범위: {min(peer_budgets):,}~{max(peer_budgets):,}원)",
                outlier=is_budget_outlier,
                evidence_notice_ids=[p["notice_id"] for p in peers]
            ))
    
    return stats


def fetch_and_compare_peers(
    plan: PurchasePlan,
    notice: PlannedNotice,
    api_key: Optional[str] = None
) -> List[BenchmarkStat]:
    """
    유사 공고를 검색하고 비교 통계를 생성합니다.
    
    Args:
        plan: 구매계획서
        notice: 생성된 공고 전략
        api_key: AI API 키
    
    Returns:
        List[BenchmarkStat]: 벤치마크 통계 리스트
    """
    print("[Peer Comparison] 유사 공고 검색 중...")
    peers = search_similar_notices_with_llm(plan, api_key)
    
    print(f"[Peer Comparison] {len(peers)}건의 유사 공고 발견")
    
    stats = compare_with_peers(notice, plan, peers)
    print(f"[Peer Comparison] {len(stats)}개 벤치마크 통계 생성 완료")
    
    return stats


if __name__ == "__main__":
    # 테스트
    from src.schema import PurchasePlan, PlannedNotice
    
    mock_plan = PurchasePlan(
        notice_name="수질측정장비 구매",
        budget_total=60_000_000,
        budget_supply=54_545_455,
        item_codes=["4111331501"],
        item_names=["TOC 측정장비"],
        contract_method_text="소액수의",
        sme_restriction_text="소기업·소상공인",
        delivery_period_text="계약일로부터 30일"
    )
    
    mock_notice = PlannedNotice(
        notice_type="소액수의",
        sme_restriction="소기업·소상공인",
        submission_period="게시일로부터 3일간",
        contract_method_sentence="소액수의(전자공개수의계약)",
        qualification_sentences=[],
        joint_contract_sentence="공동계약 불가"
    )
    
    # 벤치마크 테스트
    stats = fetch_and_compare_peers(mock_plan, mock_notice)
    print(f"\n벤치마크 통계: {len(stats)}개")
    for s in stats:
        outlier_mark = "⚠️" if s.outlier else "✓"
        print(f"  {outlier_mark} {s.field}: {s.your_value} (시장: {s.peer_summary})")
