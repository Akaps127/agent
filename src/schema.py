from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional

# 4대 파라미터는 src/parameters.py에서 중앙 관리
from src.parameters import (
    CONTRACT_LAW_TYPE,
    CONTRACT_TYPE,
    BIDDING_METHOD,
    WINNER_METHOD,
    ParameterRules
)


class PurchasePlan(BaseModel):
    notice_name: str = Field(..., description="공고명 (건명)")
    budget_total: int = Field(..., description="소요예산 (부가세 포함 총액)")
    budget_supply: int = Field(..., description="추정가격 (부가세 제외 공급가액)")
    
    # Lists instead of single strings
    item_codes: List[str] = Field(default_factory=list, description="세부품명번호 10자리 리스트 (예: ['4111331501'])")
    item_names: List[str] = Field(default_factory=list, description="대표 물품명 리스트")
    
    # 업종 관련 필드
    industry_codes: List[str] = Field(default_factory=list, description="관련 업종분류코드 리스트")
    industry_names: List[str] = Field(default_factory=list, description="업종명 리스트")
    law_basis: List[str] = Field(default_factory=list, description="근거법령 리스트")
    law_article: List[str] = Field(default_factory=list, description="법령조항 리스트")

    contract_method_text: str = Field(..., description="문서에 기재된 계약 방법 (예: '제한경쟁/소액수의')")
    
    # ===== [NEW] 4대 파라미터 필드 =====
    contract_law_type: Optional[CONTRACT_LAW_TYPE] = Field("국가계약법", description="계약법 구분: 국가계약법/지방계약법/자체기준")
    contract_type: Optional[CONTRACT_TYPE] = Field("물품구매", description="계약 유형: 공사/용역/물품/물품제조/물품구매 등")
    bidding_method: Optional[BIDDING_METHOD] = Field(None, description="입찰 방법: 일반경쟁/제한경쟁/지명경쟁/수의계약 (소액수의 시 자동으로 수의계약)")
    winner_determination: Optional[WINNER_METHOD] = Field(None, description="낙찰자결정방법: 소액수의/적격심사")
    
    # Renamed/New fields
    sme_restriction_text: Optional[str] = Field(None, description="중소기업/소상공인 제한 관련 문구")
    region_restriction_text: Optional[str] = Field(None, description="지역 제한 문구 (없으면 None)")
    joint_venture_allow: bool = Field(False, description="공동계약 허용 여부")
    # Contact Info
    project_contact: Optional[str] = Field(None, description="사업부서 담당자 정보")
    contract_contact: Optional[str] = Field(None, description="계약부서 담당자 정보")
    
    # 직접생산확인증명서 조항
    direct_production_clauses: List[str] = Field(default_factory=list, description="직접생산확인증명서 요구 조항 리스트")
    
    delivery_period_text: Optional[str] = Field(None, description="납품 기한")
    
    # 7. Bid Dates (Optional - Auto-calculated if not provided)
    bid_submission_start: Optional[str] = Field(None, description="전자입찰서 제출 시작일시 (YYYY-MM-DD HH:MM)")
    bid_submission_end: Optional[str] = Field(None, description="전자입찰서 제출 마감일시 (YYYY-MM-DD HH:MM)")
    bid_opening_datetime: Optional[str] = Field(None, description="개찰일시 (YYYY-MM-DD HH:MM)")
    bid_opening_place: Optional[str] = Field("국가종합전자조달시스템(나라장터)", description="개찰장소")
    
    @model_validator(mode='after')
    def validate_parameters(self):
        """4대 파라미터 간 조건부 로직 검증"""
        # 낙찰자결정방법이 '소액수의'이면 입찰방법을 자동으로 '수의계약'으로 설정
        if self.winner_determination == "소액수의":
            self.bidding_method = "수의계약"
        
        # 입찰방법과 낙찰자결정방법 간 유효성 검사
        if self.bidding_method and self.winner_determination:
            is_valid, error_msg = ParameterRules.validate_bidding_method(
                self.winner_determination, 
                self.bidding_method
            )
            if not is_valid:
                raise ValueError(error_msg)
        
        return self


class PlannedNotice(BaseModel):
    notice_type: str = Field(..., description="결정된 공고 유형 (소액수의, 적격심사, 일반경쟁)")
    sme_restriction: str = Field(..., description="기업제한 조건 문구")
    submission_period: str = Field(..., description="투찰 기간 문구")
    contract_method_sentence: str = Field(..., description="계약 방법 전체 문장")
    qualification_sentences: List[str] = Field(default_factory=list, description="참가자격 제한 문구 리스트")
    joint_contract_sentence: str = Field(default="공동계약 불가", description="공동계약 허용 여부 문구")
    
    # ===== [NEW] 4대 파라미터 (Writer에서 사용) =====
    contract_law_type: Optional[CONTRACT_LAW_TYPE] = Field("국가계약법", description="계약법 구분")
    contract_type: Optional[CONTRACT_TYPE] = Field("물품구매", description="계약 유형")
    bidding_method: Optional[BIDDING_METHOD] = Field(None, description="입찰 방법")
    winner_determination: Optional[WINNER_METHOD] = Field(None, description="낙찰자결정방법")
    
    # Optional fields for Writer consistency (if copied from Plan)
    notice_name: Optional[str] = None
    budget_format: Optional[str] = None
    project_contact: Optional[str] = None
    contract_contact: Optional[str] = None
    
    # Bid Date fields (calculated)
    bid_submission_start: Optional[str] = None
    bid_submission_end: Optional[str] = None
    bid_opening_datetime: Optional[str] = None
    bid_opening_place: Optional[str] = "국가종합전자조달시스템(나라장터)"


# ===== 공고문 검증 관련 스키마 =====
class LegalCitation(BaseModel):
    """법령 인용 정보"""
    law_name: str = Field(..., description="법령명 (예: 국가를 당사자로 하는 계약에 관한 법률)")
    article: Optional[str] = Field(None, description="조항 (예: 제27조)")
    url: Optional[str] = Field(None, description="법령정보센터 URL")


class LegalFinding(BaseModel):
    """법령 검증 결과 항목"""
    target_sentence: str = Field(..., description="검토 대상 문구")
    status: str = Field(..., description="판정 상태: OK, RISK, NEEDS_REVIEW")
    risk_level: str = Field("LOW", description="리스크 수준: LOW, MEDIUM, HIGH")
    reason: str = Field(..., description="판정 사유")
    citations: List[LegalCitation] = Field(default_factory=list, description="관련 법령 근거")
    suggested_rewrite: Optional[str] = Field(None, description="권고 수정 문구")


class BenchmarkStat(BaseModel):
    """나라장터 벤치마크 통계 항목"""
    field: str = Field(..., description="비교 필드명 (예: 공동계약, 지역제한)")
    your_value: str = Field(..., description="현재 공고 값")
    peer_summary: str = Field(..., description="유사 공고 통계 요약")
    outlier: bool = Field(False, description="이례 여부")
    evidence_notice_ids: List[str] = Field(default_factory=list, description="근거 공고 ID")


class AuditReport(BaseModel):
    """공고문 검증 통합 리포트"""
    notice: Optional[PlannedNotice] = Field(None, description="생성된 공고 전략")
    rule_violations: List[str] = Field(default_factory=list, description="규칙 위반 목록")
    legal_findings: List[LegalFinding] = Field(default_factory=list, description="법령 검증 결과")
    benchmark_stats: List[BenchmarkStat] = Field(default_factory=list, description="벤치마크 통계")
    overall_risk: str = Field("LOW", description="종합 리스크: LOW, MEDIUM, HIGH")
