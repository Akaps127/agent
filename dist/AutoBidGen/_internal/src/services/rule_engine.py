"""
규칙 기반 검증 엔진
- 예산-계약방법 일관성 검사
- 중소기업 제한 검사
- 기타 기본 규칙 검사
"""

from typing import List
from src.schema import PurchasePlan, PlannedNotice
from src.config import get_limit_gosi

# 예산 기준
SMALL_SUM_LIMIT = 100_000_000  # 1억


def check_rules(plan: PurchasePlan, notice: PlannedNotice) -> List[str]:
    """
    기본 규칙 기반 검증을 수행합니다.
    
    Args:
        plan: 구매계획서 데이터
        notice: 생성된 공고 전략
    
    Returns:
        List[str]: 위반 사항 목록
    """
    violations = []
    
    # 1. 예산-계약방법 일관성 검사
    if plan.budget_supply > SMALL_SUM_LIMIT and notice.notice_type == "소액수의":
        violations.append(
            f"[위험] 추정가격({plan.budget_supply:,}원)이 1억원을 초과하는데 소액수의로 분류되었습니다. "
            "계약방법을 재검토하세요."
        )
    
    if plan.budget_supply <= SMALL_SUM_LIMIT and notice.notice_type == "적격심사":
        violations.append(
            f"[주의] 추정가격({plan.budget_supply:,}원)이 1억원 이하인데 적격심사로 분류되었습니다. "
            "소액수의 적용 가능 여부를 확인하세요."
        )
    
    # 2. 중소기업 제한 검사
    gosi_limit = get_limit_gosi()
    if plan.budget_supply < gosi_limit and "일반경쟁" in notice.sme_restriction:
        violations.append(
            f"[위험] 추정가격({plan.budget_supply:,}원)이 고시금액({gosi_limit:,}원) 미만인데 "
            "중소기업 제한이 적용되지 않았습니다. 「중소기업제품 구매촉진 및 판로지원에 관한 법률」을 확인하세요."
        )
    
    # 3. 공동계약 허용 여부 검사
    if plan.joint_venture_allow and plan.budget_supply < SMALL_SUM_LIMIT:
        violations.append(
            f"[주의] 소액(1억 미만)인데 공동계약을 허용하였습니다. "
            "일반적으로 소액 건은 공동계약을 허용하지 않습니다."
        )
    
    # 4. 필수 항목 누락 검사
    if not plan.item_codes:
        violations.append("[주의] 세부품명번호(item_codes)가 입력되지 않았습니다.")
    
    if not plan.notice_name or len(plan.notice_name.strip()) < 5:
        violations.append("[위험] 공고명이 너무 짧거나 입력되지 않았습니다.")
    
    if not plan.delivery_period_text:
        violations.append("[주의] 납품기한이 입력되지 않았습니다.")
    
    return violations


if __name__ == "__main__":
    # 테스트
    from src.schema import PurchasePlan, PlannedNotice
    
    mock_plan = PurchasePlan(
        notice_name="테스트 공고",
        budget_total=60_000_000,
        budget_supply=54_545_455,
        item_codes=["4111331501"],
        item_names=["테스트 물품"],
        contract_method_text="소액수의",
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
    
    violations = check_rules(mock_plan, mock_notice)
    print(f"위반사항: {len(violations)}건")
    for v in violations:
        print(f"  - {v}")
