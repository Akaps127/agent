"""
AI 기반 법령 검증 모듈
- Claude 또는 OpenAI를 사용한 법령 위반 검사
- 기본 규칙 기반 법령 검사 (Fallback)
"""

import os
import json
from typing import List, Optional
from src.schema import PurchasePlan, PlannedNotice, LegalFinding, LegalCitation

# AI 클라이언트 초기화
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


# 법령 검사 프롬프트
LEGAL_AUDIT_PROMPT = """당신은 대한민국 조달 법무 전문가입니다. 아래 구매계획서와 공고 초안을 검토하고 법령 위반 가능성을 분석하세요.

## 구매계획서 정보
- 공고명: {notice_name}
- 추정가격: {budget_supply:,}원 (부가세 제외)
- 총예산: {budget_total:,}원 (부가세 포함)
- 계약방법: {contract_method}
- 중소기업 제한: {sme_restriction}
- 지역 제한: {region_restriction}
- 공동계약: {joint_venture}

## 공고 초안 정보
- 공고 유형: {notice_type}
- 계약방법 문장: {contract_method_sentence}
- 참가자격: {qualification_sentences}

## 검토 요청 사항
1. 예정가격 산정의 적정성
2. 입찰 방식 선택 근거의 합법성
3. 참가자격 제한의 적법성
4. 중소기업/지역 제한의 타당성
5. 공동계약 허용 여부의 적절성

## 응답 형식 (JSON)
```json
[
  {{
    "target_sentence": "검토 대상 문구",
    "status": "OK|RISK|NEEDS_REVIEW",
    "risk_level": "LOW|MEDIUM|HIGH",
    "reason": "판정 사유 (관련 법령 조항 포함)",
    "law_name": "관련 법령명 (없으면 null)",
    "article": "관련 조항 (없으면 null)",
    "suggested_rewrite": "권고 수정 문구 (없으면 null)"
  }}
]
```

JSON 배열만 응답하세요. 추가 설명은 불필요합니다.
"""


def audit_with_llm(
    plan: PurchasePlan,
    notice: PlannedNotice,
    api_key: Optional[str] = None,
    provider: str = "claude"
) -> List[LegalFinding]:
    """
    AI를 사용하여 법령 위반 검사를 수행합니다.
    
    Args:
        plan: 구매계획서
        notice: 생성된 공고 전략
        api_key: AI API 키 (None이면 환경변수에서 로드)
        provider: AI 제공자 ("claude" 또는 "openai")
    
    Returns:
        List[LegalFinding]: 법령 검토 결과 리스트
    """
    # 프롬프트 구성
    prompt = LEGAL_AUDIT_PROMPT.format(
        notice_name=plan.notice_name,
        budget_supply=plan.budget_supply,
        budget_total=plan.budget_total,
        contract_method=plan.contract_method_text,
        sme_restriction=plan.sme_restriction_text or "없음",
        region_restriction=plan.region_restriction_text or "없음",
        joint_venture="허용" if plan.joint_venture_allow else "불허",
        notice_type=notice.notice_type,
        contract_method_sentence=notice.contract_method_sentence,
        qualification_sentences=", ".join(notice.qualification_sentences) if notice.qualification_sentences else "없음"
    )
    
    # API 키 확인
    anthropic_key = api_key if provider == "claude" else os.getenv("ANTHROPIC_API_KEY")
    openai_key = api_key if provider == "openai" else os.getenv("OPENAI_API_KEY")
    
    response_text = None
    
    # Claude 호출 시도
    if ANTHROPIC_AVAILABLE and anthropic_key:
        try:
            client = anthropic.Anthropic(api_key=anthropic_key)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
            print("[Legal Audit] Claude 응답 수신 완료")
        except Exception as e:
            print(f"[Legal Audit] Claude 호출 실패: {e}")
    
    # OpenAI Fallback
    if response_text is None and OPENAI_AVAILABLE and openai_key:
        try:
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            response_text = response.choices[0].message.content
            print("[Legal Audit] OpenAI 응답 수신 완료")
        except Exception as e:
            print(f"[Legal Audit] OpenAI 호출 실패: {e}")
    
    # AI 응답 파싱
    if response_text:
        try:
            # JSON 추출 (```json ... ``` 블록 처리)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            findings_data = json.loads(response_text)
            findings = []
            for item in findings_data:
                citations = []
                if item.get("law_name"):
                    citations.append(LegalCitation(
                        law_name=item["law_name"],
                        article=item.get("article")
                    ))
                
                findings.append(LegalFinding(
                    target_sentence=item["target_sentence"],
                    status=item["status"],
                    risk_level=item.get("risk_level", "LOW"),
                    reason=item["reason"],
                    citations=citations,
                    suggested_rewrite=item.get("suggested_rewrite")
                ))
            return findings
        except json.JSONDecodeError as e:
            print(f"[Legal Audit] JSON 파싱 실패: {e}")
            print(f"[Legal Audit] 원본 응답: {response_text[:500]}")
    
    # Fallback: 기본 규칙 기반 검사
    print("[Legal Audit] AI 사용 불가. 기본 규칙 검사로 대체합니다.")
    return check_basic_legal_rules(plan, notice)


def check_basic_legal_rules(plan: PurchasePlan, notice: PlannedNotice) -> List[LegalFinding]:
    """
    AI 없이 기본 규칙 기반 법령 검사를 수행합니다.
    
    Args:
        plan: 구매계획서
        notice: 생성된 공고 전략
    
    Returns:
        List[LegalFinding]: 법령 검토 결과 리스트
    """
    findings = []
    
    # 1. 소액수의 금액 기준 검사
    if notice.notice_type == "소액수의" and plan.budget_supply > 100_000_000:
        findings.append(LegalFinding(
            target_sentence=f"소액수의 계약 (추정가격: {plan.budget_supply:,}원)",
            status="RISK",
            risk_level="HIGH",
            reason="국가계약법 시행령 제26조에 따르면 추정가격 1억원 초과 시 소액수의계약이 불가합니다.",
            citations=[LegalCitation(
                law_name="국가를 당사자로 하는 계약에 관한 법률 시행령",
                article="제26조"
            )],
            suggested_rewrite="적격심사 또는 경쟁입찰로 변경 검토 필요"
        ))
    
    # 2. 지역제한 적법성 검사
    if plan.region_restriction_text and plan.budget_supply >= 230_000_000:
        findings.append(LegalFinding(
            target_sentence=f"지역제한: {plan.region_restriction_text}",
            status="NEEDS_REVIEW",
            risk_level="MEDIUM",
            reason="추정가격이 고시금액(2.3억) 이상인 경우 지역제한 적용이 제한될 수 있습니다. 법령 검토가 필요합니다.",
            citations=[LegalCitation(
                law_name="국가를 당사자로 하는 계약에 관한 법률 시행령",
                article="제21조"
            )]
        ))
    
    # 3. 중소기업 제한 검사
    if plan.budget_supply < 230_000_000 and notice.sme_restriction and "일반경쟁" in notice.sme_restriction:
        findings.append(LegalFinding(
            target_sentence=f"중소기업 제한 미적용 (추정가격: {plan.budget_supply:,}원)",
            status="RISK",
            risk_level="HIGH",
            reason="중소기업제품 구매촉진법에 따라 고시금액 미만 공공구매는 중소기업 제한 경쟁이 원칙입니다.",
            citations=[LegalCitation(
                law_name="중소기업제품 구매촉진 및 판로지원에 관한 법률",
                article="제6조"
            )],
            suggested_rewrite="중소기업 제한 경쟁으로 변경 필요"
        ))
    
    # 4. 공동계약 허용 여부 검사
    if plan.joint_venture_allow and plan.budget_supply < 100_000_000:
        findings.append(LegalFinding(
            target_sentence="공동계약 허용",
            status="NEEDS_REVIEW",
            risk_level="LOW",
            reason="소액 건(1억 미만)에서 공동계약 허용 시 행정 효율성 검토가 필요합니다.",
            citations=[]
        ))
    
    # 문제가 없는 경우 OK 항목 추가
    if not findings:
        findings.append(LegalFinding(
            target_sentence="전체 공고문",
            status="OK",
            risk_level="LOW",
            reason="기본 규칙 검사에서 특이사항이 발견되지 않았습니다.",
            citations=[]
        ))
    
    return findings


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
    
    # 기본 규칙 검사 테스트
    findings = check_basic_legal_rules(mock_plan, mock_notice)
    print(f"법령 검토 결과: {len(findings)}건")
    for f in findings:
        print(f"  [{f.status}] {f.target_sentence}: {f.reason}")
