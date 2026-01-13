"""
4대 파라미터 정의 및 관리 모듈
공고문 생성에 필요한 계약법, 계약유형, 입찰방법, 낙찰자결정방법을 중앙 관리
"""
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field


# ===== 1. 계약법 구분 =====
CONTRACT_LAW_TYPES = ["국가계약법", "지방계약법", "자체기준"]
CONTRACT_LAW_TYPE = Literal["국가계약법", "지방계약법", "자체기준"]

CONTRACT_LAW_INFO = {
    "국가계약법": {
        "full_name": "국가를 당사자로 하는 계약에 관한 법률",
        "short_name": "국가계약법",
        "enforcement_decree": "국가를 당사자로 하는 계약에 관한 법률 시행령",
        "enforcement_rules": "국가를 당사자로 하는 계약에 관한 법률 시행규칙",
        "description": "중앙행정기관 및 중앙정부 소속 기관이 체결하는 계약"
    },
    "지방계약법": {
        "full_name": "지방자치단체를 당사자로 하는 계약에 관한 법률",
        "short_name": "지방계약법",
        "enforcement_decree": "지방자치단체를 당사자로 하는 계약에 관한 법률 시행령",
        "enforcement_rules": "지방자치단체를 당사자로 하는 계약에 관한 법률 시행규칙",
        "description": "지방자치단체가 체결하는 계약"
    },
    "자체기준": {
        "full_name": "기관 자체 계약 기준",
        "short_name": "자체기준",
        "enforcement_decree": "기관 내부 규정",
        "enforcement_rules": "기관 내부 세칙",
        "description": "특수법인이나 공공기관의 자체 계약 기준"
    }
}


# ===== 2. 계약 유형 =====
CONTRACT_TYPES = [
    "공사", 
    "용역", 
    "물품", 
    "물품제조", 
    "물품구매", 
    "외주용역", 
    "학술연구용역", 
    "시설관리용역", 
    "전문용역", 
    "기술용역"
]

CONTRACT_TYPE = Literal[
    "공사", "용역", "물품", "물품제조", "물품구매", 
    "외주용역", "학술연구용역", "시설관리용역", "전문용역", "기술용역"
]

CONTRACT_TYPE_INFO = {
    "공사": {
        "category": "공사",
        "doc_name": "공사입찰유의서",
        "general_conditions": "공사계약일반조건",
        "special_conditions": "공사계약특수조건",
        "description": "건설공사 등 시설물 건축/설치"
    },
    "용역": {
        "category": "용역",
        "doc_name": "용역입찰유의서",
        "general_conditions": "용역계약일반조건",
        "special_conditions": "용역계약특수조건",
        "description": "일반 용역 서비스"
    },
    "물품": {
        "category": "물품",
        "doc_name": "물품구매(제조)입찰유의서",
        "general_conditions": "물품구매(제조)계약일반조건",
        "special_conditions": "물품구매(제조)계약특수조건",
        "description": "일반 물품"
    },
    "물품제조": {
        "category": "물품",
        "doc_name": "물품구매(제조)입찰유의서",
        "general_conditions": "물품구매(제조)계약일반조건",
        "special_conditions": "물품구매(제조)계약특수조건",
        "description": "제조를 통한 물품 공급"
    },
    "물품구매": {
        "category": "물품",
        "doc_name": "물품구매(제조)입찰유의서",
        "general_conditions": "물품구매(제조)계약일반조건",
        "special_conditions": "물품구매(제조)계약특수조건",
        "description": "기성품 구매"
    },
    "외주용역": {
        "category": "용역",
        "doc_name": "용역입찰유의서",
        "general_conditions": "용역계약일반조건",
        "special_conditions": "용역계약특수조건",
        "description": "외부 전문가를 통한 용역"
    },
    "학술연구용역": {
        "category": "용역",
        "doc_name": "용역입찰유의서",
        "general_conditions": "용역계약일반조건",
        "special_conditions": "용역계약특수조건",
        "description": "학술 연구 관련 용역"
    },
    "시설관리용역": {
        "category": "용역",
        "doc_name": "용역입찰유의서",
        "general_conditions": "용역계약일반조건",
        "special_conditions": "용역계약특수조건",
        "description": "시설 유지보수 및 관리"
    },
    "전문용역": {
        "category": "용역",
        "doc_name": "용역입찰유의서",
        "general_conditions": "용역계약일반조건",
        "special_conditions": "용역계약특수조건",
        "description": "전문 분야 용역"
    },
    "기술용역": {
        "category": "용역",
        "doc_name": "용역입찰유의서",
        "general_conditions": "용역계약일반조건",
        "special_conditions": "용역계약특수조건",
        "description": "기술 관련 용역"
    }
}


# ===== 3. 입찰 방법 =====
BIDDING_METHODS = ["일반경쟁", "제한경쟁", "지명경쟁", "수의계약"]
BIDDING_METHOD = Literal["일반경쟁", "제한경쟁", "지명경쟁", "수의계약"]

BIDDING_METHOD_INFO = {
    "일반경쟁": {
        "description": "불특정 다수를 대상으로 하는 경쟁입찰",
        "requirements": "참가자격 제한 없음 (법령상 제한 제외)",
        "applicability": "모든 계약(소액수의 제외)"
    },
    "제한경쟁": {
        "description": "참가자격을 제한하는 경쟁입찰",
        "requirements": "특정 요건(면허, 기술능력, 실적 등) 필요",
        "applicability": "전문성 필요 계약"
    },
    "지명경쟁": {
        "description": "특정 업체를 지명하여 경쟁시키는 입찰",
        "requirements": "발주기관이 지명한 업체만 참가 가능",
        "applicability": "특수한 경우(긴급, 특허권 등)"
    },
    "수의계약": {
        "description": "경쟁 없이 계약상대자를 선정",
        "requirements": "법령상 수의계약 사유 해당",
        "applicability": "소액수의, 긴급, 특수성 등",
        "note": "낙찰자결정방법이 '소액수의'일 경우 자동 선택됨"
    }
}


# ===== 4. 낙찰자결정방법 =====
WINNER_METHODS = ["소액수의", "적격심사"]
WINNER_METHOD = Literal["소액수의", "적격심사"]

WINNER_METHOD_INFO = {
    "소액수의": {
        "description": "일정 금액 이하의 소액 계약",
        "determination": "최저가 낙찰",
        "bidding_method": "수의계약",
        "threshold_description": "추정가격이 고시금액 미만",
        "note": "입찰방법이 자동으로 '수의계약'으로 고정됨",
        "qualification_review": False
    },
    "적격심사": {
        "description": "가격과 품질을 종합 평가",
        "determination": "적격심사기준표 기준 종합평점 최고점",
        "bidding_method": "일반경쟁, 제한경쟁, 지명경쟁",
        "threshold_description": "추정가격이 별표1 ~ 별표14 기준 해당",
        "note": "계약유형별 적격심사기준표 적용",
        "qualification_review": True
    }
}


# ===== 조건부 로직 규칙 =====
class ParameterRules:
    """파라미터 간 조건부 로직 정의"""
    
    @staticmethod
    def validate_bidding_method(winner_method: str, bidding_method: str) -> tuple[bool, str]:
        """
        입찰방법 유효성 검사
        
        Returns:
            (is_valid, error_message)
        """
        if winner_method == "소액수의":
            if bidding_method != "수의계약":
                return False, "낙찰자결정방법이 '소액수의'일 경우 입찰방법은 '수의계약'이어야 합니다."
        
        if winner_method == "적격심사":
            if bidding_method == "수의계약":
                return False, "낙찰자결정방법이 '적격심사'일 경우 입찰방법은 '수의계약'일 수 없습니다."
        
        return True, ""
    
    @staticmethod
    def get_auto_bidding_method(winner_method: str) -> str | None:
        """
        낙찰자결정방법에 따른 자동 입찰방법 반환
        
        Returns:
            자동 설정되어야 할 입찰방법 (없으면 None)
        """
        if winner_method == "소액수의":
            return "수의계약"
        return None
    
    @staticmethod
    def get_available_bidding_methods(winner_method: str) -> List[str]:
        """
        낙찰자결정방법에 따라 선택 가능한 입찰방법 목록 반환
        """
        if winner_method == "소액수의":
            return ["수의계약"]  # 고정
        elif winner_method == "적격심사":
            return ["일반경쟁", "제한경쟁", "지명경쟁"]  # 수의계약 제외
        else:
            return BIDDING_METHODS  # 모두 허용
    
    @staticmethod
    def get_available_winner_methods(bidding_method: str) -> List[str]:
        """
        입찰방법에 따라 선택 가능한 낙찰자결정방법 목록 반환
        """
        if bidding_method == "수의계약":
            return ["소액수의"]  # 소액수의만 가능
        else:
            return ["적격심사"]  # 수의계약 아니면 적격심사
        

# ===== API 응답용 스키마 =====
class ParameterDefinition(BaseModel):
    """각 파라미터의 정의"""
    name: str = Field(..., description="파라미터 이름")
    display_name: str = Field(..., description="화면 표시 이름")
    values: List[str] = Field(..., description="선택 가능한 값 목록")
    info: Dict[str, Any] = Field(default_factory=dict, description="각 값에 대한 상세 정보")
    default: str | None = Field(None, description="기본값")


class ParametersResponse(BaseModel):
    """4대 파라미터 전체 응답"""
    contract_law_types: ParameterDefinition
    contract_types: ParameterDefinition
    bidding_methods: ParameterDefinition
    winner_methods: ParameterDefinition


def get_parameters_definition() -> ParametersResponse:
    """
    프론트엔드에서 사용할 4대 파라미터 정의를 반환
    """
    return ParametersResponse(
        contract_law_types=ParameterDefinition(
            name="contract_law_type",
            display_name="계약법 구분",
            values=CONTRACT_LAW_TYPES,
            info=CONTRACT_LAW_INFO,
            default="국가계약법"
        ),
        contract_types=ParameterDefinition(
            name="contract_type",
            display_name="계약 유형",
            values=CONTRACT_TYPES,
            info=CONTRACT_TYPE_INFO,
            default="물품구매"
        ),
        bidding_methods=ParameterDefinition(
            name="bidding_method",
            display_name="입찰 방법",
            values=BIDDING_METHODS,
            info=BIDDING_METHOD_INFO,
            default=None
        ),
        winner_methods=ParameterDefinition(
            name="winner_determination",
            display_name="낙찰자결정방법",
            values=WINNER_METHODS,
            info=WINNER_METHOD_INFO,
            default=None
        )
    )


# ===== 유틸리티 함수 =====
def get_law_text(contract_law_type: str, key: str) -> str:
    """계약법 구분에 따른 법령 문구 반환"""
    law_info = CONTRACT_LAW_INFO.get(contract_law_type, CONTRACT_LAW_INFO["국가계약법"])
    return law_info.get(key, "")


def get_contract_type_doc(contract_type: str) -> str:
    """계약 유형에 따른 입찰유의서 명칭 반환"""
    type_info = CONTRACT_TYPE_INFO.get(contract_type, CONTRACT_TYPE_INFO["물품구매"])
    return type_info.get("doc_name", "물품구매(제조)입찰유의서")


def get_contract_conditions(contract_type: str) -> tuple[str, str]:
    """계약 유형에 따른 일반조건/특수조건 명칭 반환"""
    type_info = CONTRACT_TYPE_INFO.get(contract_type, CONTRACT_TYPE_INFO["물품구매"])
    return (
        type_info.get("general_conditions", "물품구매(제조)계약일반조건"),
        type_info.get("special_conditions", "물품구매(제조)계약특수조건")
    )
