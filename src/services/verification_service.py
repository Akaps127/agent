"""
공고문 검증 통합 서비스
- 규칙 기반 검증
- AI 기반 법령 검증
- 나라장터 비교 검증
- 통합 리포트 생성
"""

import os
from typing import Optional
from src.schema import (
    PurchasePlan, 
    PlannedNotice, 
    AuditReport, 
    LegalFinding, 
    BenchmarkStat
)
from src.nodes.planner import plan_notice
from src.services.rule_engine import check_rules
from src.services.legal_audit import audit_with_llm, check_basic_legal_rules
from src.services.peer_comparison import fetch_and_compare_peers


class NoticeVerificationService:
    """
    공고문 검증 통합 서비스
    
    사용법:
        service = NoticeVerificationService()
        report = service.verify_notice(purchase_plan)
        print(report.model_dump_json(indent=2))
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        초기화
        
        Args:
            api_key: AI API 키 (None이면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.ai_available = bool(self.api_key)
        
        print(f"[검증 서비스 초기화]")
        print(f"  - AI 검증: {'사용 가능' if self.ai_available else '사용 불가 (기본 규칙 사용)'}")
    
    def verify_notice(
        self,
        plan: PurchasePlan,
        notice: Optional[PlannedNotice] = None,
        enable_legal_check: bool = True,
        enable_peer_comparison: bool = True
    ) -> AuditReport:
        """
        공고문 전체 검증을 수행합니다.
        
        Args:
            plan: 구매계획서
            notice: 생성된 공고 전략 (None이면 자동 생성)
            enable_legal_check: 법령 검증 활성화 여부
            enable_peer_comparison: 나라장터 비교 활성화 여부
        
        Returns:
            AuditReport: 통합 검증 리포트
        """
        print("\n[공고문 검증 시작]")
        
        # 1. 공고 초안 생성 (없으면)
        if notice is None:
            print("  1️⃣ 공고 초안 생성 중...")
            notice = plan_notice(plan)
        print(f"     ✓ 공고 유형: {notice.notice_type}")
        
        # 2. 기본 규칙 검증
        print("  2️⃣ 기본 규칙 검증 중...")
        violations = check_rules(plan, notice)
        print(f"     ✓ 규칙 위반: {len(violations)}건")
        
        # 3. 법령 검증
        legal_findings = []
        if enable_legal_check:
            print("  3️⃣ 법령 검증 중...")
            legal_findings = self._run_legal_check(plan, notice)
            print(f"     ✓ 법령 검토: {len(legal_findings)}건")
        else:
            print("  3️⃣ 법령 검증 건너뜀")
        
        # 4. 나라장터 비교
        benchmark_stats = []
        if enable_peer_comparison:
            print("  4️⃣ 나라장터 비교 중...")
            benchmark_stats = self._run_peer_comparison(plan, notice)
            print(f"     ✓ 벤치마크: {len(benchmark_stats)}건")
        else:
            print("  4️⃣ 나라장터 비교 건너뜀")
        
        # 5. 종합 리스크 계산
        overall_risk = self._calculate_overall_risk(violations, legal_findings, benchmark_stats)
        
        # 6. 통합 리포트 생성
        report = AuditReport(
            notice=notice,
            rule_violations=violations,
            legal_findings=legal_findings,
            benchmark_stats=benchmark_stats,
            overall_risk=overall_risk
        )
        
        print(f"\n[검증 완료] 종합 리스크: {report.overall_risk}")
        return report
    
    def _run_legal_check(self, plan: PurchasePlan, notice: PlannedNotice):
        """법령 검증 실행 (내부 메서드)"""
        try:
            if self.ai_available:
                findings = audit_with_llm(plan, notice, self.api_key)
                
                # 기본 규칙 검사 추가 (중복 제거)
                basic_findings = check_basic_legal_rules(plan, notice)
                existing_targets = {f.target_sentence for f in findings}
                for bf in basic_findings:
                    if bf.target_sentence not in existing_targets:
                        findings.append(bf)
                
                return findings
            else:
                return check_basic_legal_rules(plan, notice)
        except Exception as e:
            print(f"     ⚠️ 법령 검증 오류: {e}")
            try:
                return check_basic_legal_rules(plan, notice)
            except:
                return []
    
    def _run_peer_comparison(self, plan: PurchasePlan, notice: PlannedNotice):
        """나라장터 비교 실행 (내부 메서드)"""
        try:
            return fetch_and_compare_peers(plan, notice, self.api_key)
        except Exception as e:
            print(f"     ⚠️ 나라장터 비교 오류: {e}")
            return []
    
    def _calculate_overall_risk(
        self,
        violations: list,
        legal_findings: list,
        benchmark_stats: list
    ) -> str:
        """종합 리스크 계산"""
        risk_score = 0
        
        # 규칙 위반 점수
        for v in violations:
            if "[위험]" in v:
                risk_score += 3
            elif "[주의]" in v:
                risk_score += 1
        
        # 법령 검토 점수
        for f in legal_findings:
            if f.status == "RISK":
                if f.risk_level == "HIGH":
                    risk_score += 4
                elif f.risk_level == "MEDIUM":
                    risk_score += 2
                else:
                    risk_score += 1
            elif f.status == "NEEDS_REVIEW":
                risk_score += 1
        
        # 벤치마크 점수
        outlier_count = sum(1 for s in benchmark_stats if s.outlier)
        if outlier_count >= 3:
            risk_score += 2
        elif outlier_count >= 1:
            risk_score += 1
        
        # 종합 판정
        if risk_score >= 6:
            return "HIGH"
        elif risk_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def print_summary(self, report: AuditReport) -> None:
        """리포트 요약 출력"""
        print("\n" + "="*60)
        print("검증 결과 요약")
        print("="*60)
        
        if report.notice:
            print(f"\n📋 공고명: {report.notice.notice_name or '(미정)'}")
            print(f"📌 공고 유형: {report.notice.notice_type}")
        print(f"⚠️ 종합 리스크: {report.overall_risk}")
        
        # 규칙 위반
        print(f"\n1️⃣ 규칙 위반: {len(report.rule_violations)}건")
        for i, v in enumerate(report.rule_violations[:3], 1):
            print(f"   {i}. {v}")
        if len(report.rule_violations) > 3:
            print(f"   ... 외 {len(report.rule_violations) - 3}건")
        
        # 법령 검토
        print(f"\n2️⃣ 법령 검토: {len(report.legal_findings)}건")
        risk_counts = {"OK": 0, "RISK": 0, "NEEDS_REVIEW": 0}
        for finding in report.legal_findings:
            risk_counts[finding.status] = risk_counts.get(finding.status, 0) + 1
        
        print(f"   - OK: {risk_counts['OK']}건")
        print(f"   - RISK: {risk_counts['RISK']}건")
        print(f"   - NEEDS_REVIEW: {risk_counts['NEEDS_REVIEW']}건")
        
        # 고위험 항목 출력
        high_risks = [f for f in report.legal_findings if f.risk_level == "HIGH"]
        if high_risks:
            print(f"\n   ⚠️ 고위험 항목:")
            for i, f in enumerate(high_risks[:3], 1):
                print(f"   {i}. {f.target_sentence[:50]}...")
        
        # 벤치마크
        print(f"\n3️⃣ 나라장터 비교: {len(report.benchmark_stats)}건")
        outliers = [s for s in report.benchmark_stats if s.outlier]
        if outliers:
            print(f"   ⚠️ 이례적 항목: {len(outliers)}건")
            for i, s in enumerate(outliers, 1):
                print(f"   {i}. {s.field}: {s.your_value}")
        else:
            print(f"   ✓ 모든 항목이 시장 평균 범위 내")
        
        print("\n" + "="*60)


if __name__ == "__main__":
    # 테스트
    from src.schema import PurchasePlan
    
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
    
    # 검증 서비스 실행
    service = NoticeVerificationService()
    report = service.verify_notice(mock_plan)
    service.print_summary(report)
