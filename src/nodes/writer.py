from datetime import datetime
from types import SimpleNamespace
from src.schema import PurchasePlan, PlannedNotice
from src.config import get_limit_gosi

# [TODO] 추후 외부 API(기재부 고시) 연동 예정
LIMIT_SMALL = 100_000_000   # 1억 원 (소기업 제한 기준)
# LIMIT_GOSI replaced by dynamic config

# ===== 법령 문구 상수 (계약법 구분에 따라 변경) =====
LAW_TEXTS = {
    "국가계약법": {
        "full_name": "국가를 당사자로 하는 계약에 관한 법률",
        "short_name": "국가계약법",
        "시행령": "국가를 당사자로 하는 계약에 관한 법률 시행령",
        "시행규칙": "국가를 당사자로 하는 계약에 관한 법률 시행규칙",
        "부정당업자조항": "제27조",
        "부정당업자조항_금품": "제27조 제1항 제7호",
        "부정당업자조항_담합": "제27조 제1항 제2호",
        "조세포탈조항": "제27조의5",
        "시행령_조세포탈": "제12조제3항",
        "입찰무효조항_시행령": "제39조제4항",
        "입찰무효조항_규칙": "제44조",
        "청렴조항_시행령": "제4조의2 제1항 제2호",
    },
    "지방계약법": {
        "full_name": "지방자치단체를 당사자로 하는 계약에 관한 법률",
        "short_name": "지방계약법",
        "시행령": "지방자치단체를 당사자로 하는 계약에 관한 법률 시행령",
        "시행규칙": "지방자치단체를 당사자로 하는 계약에 관한 법률 시행규칙",
        "부정당업자조항": "제31조",
        "부정당업자조항_금품": "제31조 제1항 제7호",
        "부정당업자조항_담합": "제31조 제1항 제2호",
        "조세포탈조항": "제31조의5",
        "시행령_조세포탈": "제13조제3항",
        "입찰무효조항_시행령": "제42조제4항",
        "입찰무효조항_규칙": "제46조",
        "청렴조항_시행령": "제4조의2 제1항 제2호",
    },
    "자체기준": {
        "full_name": "기관 자체 계약 기준",
        "short_name": "자체기준",
        "시행령": "기관 자체 계약 기준",
        "시행규칙": "기관 자체 계약 기준",
        "부정당업자조항": "해당 조항",
        "부정당업자조항_금품": "해당 조항",
        "부정당업자조항_담합": "해당 조항",
        "조세포탈조항": "해당 조항",
        "시행령_조세포탈": "해당 조항",
        "입찰무효조항_시행령": "해당 조항",
        "입찰무효조항_규칙": "해당 조항",
        "청렴조항_시행령": "해당 조항",
    }
}

# 계약 유형별 입찰유의서 명칭
CONTRACT_TYPE_DOCS = {
    "공사": "공사입찰유의서",
    "용역": "용역입찰유의서",
    "물품": "물품구매(제조)입찰유의서",
    "물품제조": "물품구매(제조)입찰유의서",
    "물품구매": "물품구매(제조)입찰유의서",
    "외주용역": "용역입찰유의서",
    "학술연구용역": "학술연구용역입찰유의서",
    "시설관리용역": "용역입찰유의서",
    "전문용역": "용역입찰유의서",
    "기술용역": "용역입찰유의서",
}

# 계약 유형별 일반조건/특수조건 명칭
CONTRACT_TYPE_CONDITIONS = {
    "공사": ("공사계약일반조건", "공사계약특수조건"),
    "용역": ("용역계약일반조건", "용역계약특수조건"),
    "물품": ("물품구매(제조)계약일반조건", "물품구매(제조)계약특수조건"),
    "물품제조": ("물품구매(제조)계약일반조건", "물품구매(제조)계약특수조건"),
    "물품구매": ("물품구매(제조)계약일반조건", "물품구매(제조)계약특수조건"),
    "외주용역": ("용역계약일반조건", "용역계약특수조건"),
    "학술연구용역": ("학술연구용역계약일반조건", "학술연구용역계약특수조건"),
    "시설관리용역": ("용역계약일반조건", "용역계약특수조건"),
    "전문용역": ("용역계약일반조건", "용역계약특수조건"),
    "기술용역": ("용역계약일반조건", "용역계약특수조건"),
}


def write_notice(purchase_plan: PurchasePlan, planned_notice: PlannedNotice) -> str:
    """
    [Phase 4 Final Polish] Writer Module - Strict Template Engine
    4가지 파라미터(계약법, 계약유형, 입찰방법, 낙찰자결정방법)를 반영하여 공고문 생성
    """
    
    # --- 0. 4대 파라미터 결정 ---
    # 우선순위: PlannedNotice > PurchasePlan > 기본값
    contract_law = planned_notice.contract_law_type or getattr(purchase_plan, 'contract_law_type', None) or "국가계약법"
    contract_type = planned_notice.contract_type or getattr(purchase_plan, 'contract_type', None) or "물품구매"
    winner_method = planned_notice.winner_determination or getattr(purchase_plan, 'winner_determination', None) or planned_notice.notice_type
    
    # 소액수의 시 입찰방법 = 수의계약 강제
    if winner_method == "소액수의":
        bidding_method = "수의계약"
    else:
        bidding_method = planned_notice.bidding_method or getattr(purchase_plan, 'bidding_method', None) or "제한경쟁"
    
    # 법령 텍스트 가져오기
    law = LAW_TEXTS.get(contract_law, LAW_TEXTS["국가계약법"])
    bid_doc = CONTRACT_TYPE_DOCS.get(contract_type, "물품구매(제조)입찰유의서")
    general_cond, special_cond = CONTRACT_TYPE_CONDITIONS.get(contract_type, ("물품구매(제조)계약일반조건", "물품구매(제조)계약특수조건"))
    
    # --- 1. Data Preparation (Field Mapping for Schema Compatibility) ---
    data = SimpleNamespace()
    
    # Field Mapping: Schema uses different names than reference code
    data.winning_method = winner_method
    data.bidding_method = bidding_method
    data.item_codes = purchase_plan.item_codes
    data.industry_info = getattr(purchase_plan, 'industry_info', [])
    item_names_raw = getattr(purchase_plan, 'item_names', [])
    if isinstance(item_names_raw, list):
        data.item_names = ", ".join(item_names_raw) if item_names_raw else "물품"
    else:
        data.item_names = item_names_raw or "물품"
    data.company_restriction = purchase_plan.sme_restriction_text
    data.joint_contract_allow = purchase_plan.joint_venture_allow
    
    # Validation/Fallback for winning_rate
    winning_rate = getattr(purchase_plan, 'winning_rate', None)
    if winning_rate:
        data.winning_rate = winning_rate
    else:
        data.winning_rate = "88" if data.winning_method == "소액수의" else "84.245"
        
    data.delivery_term = purchase_plan.delivery_period_text

    # Logic for Section 2 - 입찰방법에 따른 문구
    if data.winning_method == "소액수의":
        data.contract_method_sentence = "소액수의(총액, 전자) 대상입니다."
    elif bidding_method == "제한경쟁":
        data.contract_method_sentence = "제한경쟁(총액), 전자입찰대상 물품입니다."
    elif bidding_method == "일반경쟁":
        data.contract_method_sentence = "일반경쟁(총액), 전자입찰대상 물품입니다."
    elif bidding_method == "지명경쟁":
        data.contract_method_sentence = "지명경쟁(총액), 전자입찰대상 물품입니다."
    else:
        data.contract_method_sentence = f"{bidding_method}(총액), 전자입찰대상 물품입니다."
    
    # 적격심사 관련 문구
    if data.winning_method == "소액수의":
         data.qualification_ref = "제외대상입니다."
    else:
         q_val = planned_notice.qualification_sentences[0] if planned_notice.qualification_sentences else ""
         data.qualification_ref = f"대상 물품입니다. <span class='var'>{q_val}</span> 적용"

    # Restriction Details Logic (Section 3 - 라) -> Budget-Based Switching
    budget_supply = purchase_plan.budget_supply
    
    if budget_supply < LIMIT_SMALL:
        # Case A: 소기업 (< 1억)
        restriction_detail_html = f"""
        <div class="indent-1">라. <span class="var">소기업·소상공인</span> 제한 경쟁입니다.</div>
        <div class="indent-2" style="text-align: justify;">
            ○ 소기업 제한 : 「중소기업기본법」 제2조에 따른 소기업 또는 「소상공인 보호 및 지원에 관한 법률」 제2조에 따른 소상공인으로서 「중소기업 범위 및 확인에 관한 규정」에 따라 발급된 <span class="var">소기업·소상공인확인서</span> (전자입찰서 제출마감일 전일까지 발급된 것으로 유효기간내 있어야 함)를 소지한 업체이어야 합니다.
        </div>
        <div class="indent-2" style="text-align: justify; margin-top: 5px;">
            ※ 「중소기업제품 구매촉진 및 판로지원에 관한 법률」 제33조 제1항에 따라 소기업으로 간주되는 특별법인으로 중소기업제품 「공공구매제도 운영요령」 제45조에 따라 '특별법인 소기업 간주확인서'를 소기업 또는 소상공인으로 발급받은 경우 입찰참가 자격이 있으며 상기 각 호의 입찰참가자격을 모두 갖추어야 합니다.
        </div>
        <div class="indent-2" style="text-align: justify; margin-top: 5px;">
            ※ &lt;중소기업·소상공인확인서&gt;는 중소기업공공구매 종합정보망에서 확인하며 확인되지 않을 경우 입찰참가자격이 없습니다.
        </div>
        """
    elif budget_supply < get_limit_gosi():
        # Case B: 중소기업 (1억 ~ 2.3억)
        restriction_detail_html = f"""
        <div class="indent-1">라. <span class="var">중소기업·소상공인</span> 제한 경쟁입니다.</div>
        <div class="indent-2" style="text-align: justify;">
            ○ 중소기업 제한 : 「중소기업기본법」 제2조에 따른 중소기업 또는 「소상공인 보호 및 지원에 관한 법률」 제2조에 따른 소상공인으로서 「중소기업 범위 및 확인에 관한 규정」에 따라 발급된 <span class="var">중소기업·소상공인확인서</span> (전자입찰서 제출마감일 전일까지 발급된 것으로 유효기간내 있어야 함)를 소지한 업체이어야 합니다.
        </div>
        <div class="indent-2" style="text-align: justify; margin-top: 5px;">
            ※ 「중소기업제품 구매촉진 및 판로지원에 관한 법률」 제33조 제1항에 따라 소기업으로 간주되는 특별법인으로 중소기업제품 「공공구매제도 운영요령」 제45조에 따라 '특별법인 소기업 간주확인서'를 소기업 또는 소상공인으로 발급받은 경우 입찰참가 자격이 있으며 상기 각 호의 입찰참가자격을 모두 갖추어야 합니다.
        </div>
        <div class="indent-2" style="text-align: justify; margin-top: 5px;">
            ※ &lt;중소기업·소상공인확인서&gt;는 중소기업공공구매 종합정보망에서 확인하며 확인되지 않을 경우 입찰참가자격이 없습니다.
        </div>
        """
    else:
        # Case C: 제한 없음 (>= 2.3억)
        restriction_detail_html = """<div class="indent-1">라. 본 입찰은 기업구분에 따른 입찰참가 제한이 없습니다.</div>"""

    if "달력" in data.item_names:
        restriction_detail_html += """
        <div class="indent-2" style="text-align: justify; margin-top: 5px;">
            ○ 「중소기업제품 구매촉진 및 판로지원에 관한 법률」 제9조 및 동법 시행규칙 제5조 규정에 의한 직접생산확인증명서[세부품명번호 : 달력(4411200201)]를 소지한 자(개찰일 전일까지 발급된 것으로 유효기간 내에 있어야 함)
        </div>
        """

    # Contact Info Helper
    def parse_contact(contact):
        # Default values
        info = {
            "dept": "본사 및 소속기관 사업부서",
            "name": "담당자", 
            "tel": ""
        }
        
        if not contact:
            return info
            
        # If it's a string, try to put it in name or handle simply
        if isinstance(contact, str):
            info["name"] = contact
            return info

        # If it's an object or dict
        if isinstance(contact, dict):
            if contact.get("department"): info["dept"] = contact.get("department")
            if contact.get("name"): info["name"] = contact.get("name")
            if contact.get("phone"): info["tel"] = contact.get("phone")
        else: # Pydantic model or similar
            if hasattr(contact, "department") and contact.department: info["dept"] = contact.department
            if hasattr(contact, "name") and contact.name: info["name"] = contact.name
            if hasattr(contact, "phone") and contact.phone: info["tel"] = contact.phone
            
        return info

    project_info = parse_contact(purchase_plan.project_contact)
    data.project_contact_dept = project_info["dept"]
    data.project_contact_name = project_info["name"]
    data.project_contact_tel = project_info["tel"]

    contract_info = parse_contact(planned_notice.contract_contact)
    data.contract_contact_dept = contract_info["dept"] or "경영지원처 계약부" 
    data.contract_contact_name = contract_info["name"]
    data.contract_contact_tel = contract_info["tel"]

    # Other variables
    raw_name = purchase_plan.notice_name or ""
    clean_notice_name = raw_name.replace("계획(안)", "").replace("계획안", "").strip()
    formatted_budget = f"{purchase_plan.budget_total:,}"
    
    # [New] Date Formatting Logic (Smart G2B Style)
    def format_g2b_date(date_str):
        if not date_str: return ""
        try:
            dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M")
            return dt.strftime("%Y. %m. %d.(%H:%M)")
        except ValueError:
            return date_str

    submission_period_text = ""
    opening_date_text = ""

    if purchase_plan.bid_submission_start and purchase_plan.bid_submission_end:
        start_str = format_g2b_date(purchase_plan.bid_submission_start)
        end_str = format_g2b_date(purchase_plan.bid_submission_end)
        
        # Smart Year Omission: if same year, remove year from end date
        if len(start_str) > 4 and len(end_str) > 4 and start_str[:4] == end_str[:4]:
            end_str_short = end_str[6:] # Remove 'YYYY. ' (6 chars)
            submission_period_text = f"{start_str} ~ {end_str_short}"
        else:
            submission_period_text = f"{start_str} ~ {end_str}"
    else:
        submission_period_text = "공고서 참조"

    if purchase_plan.bid_opening_datetime:
        opening_date_text = format_g2b_date(purchase_plan.bid_opening_datetime)
    else:
         opening_date_text = "입찰서 제출 마감일 직후"

    # For section 1 references
    data.submission_period_text = submission_period_text
    data.opening_date_text = opening_date_text

    # [Contact Info Formatting Logic]
    sec1_tel = data.project_contact_tel or "000-0000-0000"
    
    def format_sec10(dept, name, tel):
        parts = []
        if dept: parts.append(dept)
        if name: parts.append(name)
        base = " ".join(parts)
        if tel:
            return f"{base} (☎{tel})"
        return base

    sec10_project = format_sec10(data.project_contact_dept, data.project_contact_name, data.project_contact_tel)
    sec10_contract = format_sec10(data.contract_contact_dept, data.contract_contact_name, data.contract_contact_tel)

    today_str = datetime.now().strftime("%Y년 %m월 %d일")

    # Title - 계약유형 및 낙찰자결정방법에 따라 변경
    if data.winning_method == "소액수의":
        title = "소액수의 견적제출 공고"
    else:
        # 계약유형에 따른 제목
        if contract_type in ["공사"]:
            title = "공사 입찰공고"
        elif contract_type in ["용역", "외주용역", "학술연구용역", "시설관리용역", "전문용역", "기술용역"]:
            title = "용역 입찰공고"
        else:
            title = "물품구매 입찰공고"

    # [Dynamic HTML Generation for Lists]
    
    # 1. Item Codes Rows - 첫 번째 품명/코드만 표시
    item_rows_html = ""
    if data.item_codes:
        item_rows_html += '<div class="indent-1">가. 국가종합전자조달시스템 입찰참가자격등록규정에 따라 반드시 전자입찰서 제출 마감일 전일까지 나라장터(G2B)시스템에 아래의 사항을 모두 입찰참가자격으로 등록한 자</div>'
        
        # 첫 번째 품명과 코드만 사용
        code = data.item_codes[0] if isinstance(data.item_codes, list) else data.item_codes
        i_name = "물품"
        if isinstance(data.item_names, list) and data.item_names:
            i_name = data.item_names[0]
        elif isinstance(data.item_names, str):
            i_name = data.item_names

        item_rows_html += f"""
        <div class="indent-2">
            ○ 입찰참가 등록 마감일 기준 <span class="var">{i_name}</span>(세부품명번호 10자리 <span class="var">{code}</span>)를 제조 또는 공급 물품으로 입찰참가 등록한 자
        </div>"""
    else:
         item_rows_html = """
        <div class="indent-1">가. 국가종합전자조달시스템 입찰참가자격등록규정에 따라 반드시 전자입찰서 제출 마감일 전일까지 나라장터(G2B)시스템에 아래의 사항을 모두 입찰참가자격으로 등록한 자</div>
        <div class="indent-2">○ 세부품명번호(10자리)를 제조 또는 공급 물품으로 입찰참가 등록한 자</div>"""

    # Industry Codes Rows Logic - 첫 번째 업종만 표시
    industry_rows_html = ""
    
    if hasattr(data, 'industry_info') and data.industry_info:
        # 첫 번째 업종 정보만 사용
        info = data.industry_info[0]
        code = info.industry_code
        name = info.industry_name
        law_name = info.legal_bases[0]['name'] if info.legal_bases and len(info.legal_bases) > 0 else "관련 법령"
        
        if name:
            industry_rows_html += f"""
        <div class="indent-2">
            ○ 「<span class="var">{law_name}</span>」에 의한 <span class="var">{name}</span>(업종코드: <span class="var">{code}</span>)으로 입찰참가 등록한 자
        </div>"""
        else:
            industry_rows_html += f"""
        <div class="indent-2">
            ○ 관련 법령에 따른 업종코드 <span class="var">{code}</span>를 등록한 자
        </div>"""

    elif hasattr(purchase_plan, 'industry_names') and purchase_plan.industry_names and purchase_plan.industry_codes:
        # 첫 번째 업종코드와 업종명만 사용
        code = purchase_plan.industry_codes[0] if isinstance(purchase_plan.industry_codes, list) else purchase_plan.industry_codes
        ind_name = purchase_plan.industry_names[0] if isinstance(purchase_plan.industry_names, list) else purchase_plan.industry_names
        
        industry_rows_html += f"""
        <div class="indent-2">
            ○ 관련 법령에 따른 <span class="var">{ind_name}</span>(업종코드: <span class="var">{code}</span>)를 등록한 자
        </div>"""
                
    elif hasattr(purchase_plan, 'industry_codes') and purchase_plan.industry_codes:
        # 첫 번째 코드만 사용
        code = purchase_plan.industry_codes[0] if isinstance(purchase_plan.industry_codes, list) else purchase_plan.industry_codes
        industry_rows_html += f"""
        <div class="indent-2">
            ○ 관련 법령에 따른 업종코드 <span class="var">{code}</span>를 등록한 자
        </div>"""
    else:
         industry_rows_html = '<div class="indent-2">○ 관련 법령에 따른 업종등록을 필한 자</div>'

    # Direct Production Logic (From Planner)
    direct_production_html = ""
    if planned_notice.qualification_sentences:
        for q in planned_notice.qualification_sentences:
            if "직접생산확인증명서" in q:
                # Remove numbering if present (planner adds '③ ')
                content = q.replace("③ ", "").replace("3. ", "").strip()
                direct_production_html += f"""
        <div class="indent-2">
            ○ <span class="var">{content}</span>
        </div>"""

    # --- 2. HTML Template (법령 문구 동적 적용) ---
    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: A4; margin: 20mm; }}
        body {{
            font-family: "Malgun Gothic", "Gulim", sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #000;
            width: 210mm; 
            margin: 0 auto;
            padding: 20mm;
            box-sizing: border-box;
            background-color: white;
        }}
        
        .var {{ color: blue; font-weight: bold; }}
        .header {{
            text-align: center; font-size: 22pt; font-weight: bold; letter-spacing: -1px;
            margin-bottom: 30px; margin-top: 10px;
        }}
        .sub-header {{ text-align: right; font-size: 10pt; margin-bottom: 10px; }}
        .section-title {{ font-weight: bold; margin-top: 25px; margin-bottom: 10px; font-size: 12pt; }}
        
        .indent-1 {{
            margin-left: 20px;
            text-indent: -20px;
            margin-bottom: 5px;
        }}
        .indent-2 {{
            margin-left: 40px;
            text-indent: -20px;
            margin-bottom: 3px;
        }}
        
        .integrity-box {{
            border: 2px solid #000;
            padding: 15px;
            margin-bottom: 30px;
            font-size: 10.5pt;
            text-align: justify;
            line-height: 1.5;
        }}
        .integrity-title {{
            display: block; text-align: center; font-weight: bold; margin-bottom: 10px; font-size: 11pt;
        }}
        .inner-box {{
            border: 1px solid #000;
            padding: 10px;
            margin: 10px 0;
            font-size: 10pt;
        }}
        .integrity-text {{
            text-align: justify;
            line-height: 1.5;
            margin-top: 10px;
        }}
        .footer {{
            text-align: center; font-size: 15pt; font-weight: bold; margin-top: 50px; margin-bottom: 50px;
        }}
    </style>
    </head>
    <body>
    
        <div class="header">{title}</div>
        <div class="sub-header">한국환경공단 입찰공고번호 : 00-00000000-00</div>

        <!-- Integrity Pledge (법령에 따라 동적 변경) -->
        <div class="integrity-box">
            <div class="integrity-title">&lt; 본 계약은 청렴계약제가 적용됩니다 &gt;</div>
            <div style="margin-bottom: 10px;">
                이 계약은 「{law["full_name"]}」 또는 「지방자치단체를 당사자로 하는 계약에 관한 법률」에 따른 청렴계약제가 적용됩니다. 입찰자는 반드시 입찰서 제출 시 아래 청렴계약서에 관한 내용을 숙지·승낙하여야 하며, 동 내용을 위반한 경우 발주기관의 조치에 대해서 어떠한 이의도 제기할 수 없습니다.
            </div>
            <div class="integrity-text">
                「{law["full_name"]}」 또는 「지방자치단체를 당사자로 하는 계약에 관한 법률」에 따라 본 입찰에 참여한 당사 대리인과 임직원은 입찰·낙찰, 계약 체결 및 이행, 감독, 검사 등의 과정(준공·납품 이후를 포함한다)에서 아래 각호의 청렴계약 조건을 준수할 것이며, 이를 위반한 때에는 입찰·낙찰을 취소하거나 계약을 해제·해지하는 등의 불이익을 감수하고, 이에 민·형사상 이의를 제기하지 않을 것임을 약정합니다.
                <br><br>
                1. 금품·향응 등(친인척 등에 대한 부정한 취업 제공 포함)을 요구 또는 약속하거나 수수(授受)하지 않을 것이며, 관계공무원에게 금품, 향응 등을 제공한 경우에는 「{law["full_name"]}」{law["부정당업자조항_금품"]} 또는 「지방자치단체를 당사자로 하는 계약에 관한 법률」제31조 제1항 제7호에 따른 부정당업자의 입찰참가자격 제한 처분을 받겠습니다.
                <br><br>
                2. 입찰가격의 사전 협의 또는 특정인의 낙찰을 위한 담합 등 공정한 경쟁을 방해하는 행위시에는 「{law["full_name"]}」{law["부정당업자조항_담합"]} 또는 「지방자치단체를 당사자로 하는 계약에 관한 법률」 제31조 제1항 제2호에 따른 부정당업자 입찰참가자격 제한 처분을 받겠습니다.
                
                <div class="inner-box">
                    우리 공단은 입찰담합 방지 및 공정거래질서 확립을 위해 「독점규제 및 공정거래에 관한 법률」에 따라 입찰담합징후분석시스템에 입찰정보를 제공하고 있습니다. 입찰담합징후 발견 시 공정거래위원회 제보 및 경찰 조사의뢰 등을 검토·시행하고 있으며, 입찰담합으로 판명시 부정당업자 제재(입찰참가자격제한) 처분 및 손해배상청구소송 제소 등 법적 제재조치를 시행하고 있습니다.
                </div>

                3. 공정한 직무수행을 방해하는 알선·청탁을 통하여 입찰 또는 계약과 관련된 특정 정보의 제공을 요구하거나 받는 행위를 하지 않겠습니다.
                <br><br>
                4. 「{law["시행령"]}」 {law["청렴조항_시행령"]} 위반 시에 아래의 손해배상액을 납부토록 하겠습니다.<br>
                &nbsp;&nbsp;- 입찰자 : 입찰금액의 100분의 5<br>
                &nbsp;&nbsp;- 계약상대자 : 계약금액의 100분의 10
            </div>
        </div>
        
        <!-- Section 1 -->
        <div class="section-title">1. 견적(입찰)에 부치는 사항</div>
        <div class="indent-1">가. 공고명 : <span class="var">{clean_notice_name}</span></div>
        <div class="indent-1">나. 계약기간 : <span class="var">{data.delivery_term}</span></div>
        <div class="indent-1">다. 예산액 : <span class="var">{formatted_budget}원</span>(부가가치세 포함)</div>
        <div class="indent-1">라. 구매범위 : 물품규격서 등 참조(문의 ☎<span class="var">{sec1_tel}</span>, <span class="var">{data.project_contact_name}</span>)</div>
        <div class="indent-1">마. 전자입찰서 제출기간 : <span class="var">{data.submission_period_text}</span></div>
        <div class="indent-1">바. 개찰일시 및 장소 : <span class="var">{data.opening_date_text}</span>, 국가종합전자조달시스템(나라장터)</div>

        <div class="section-title">2. 견적(입찰) 및 계약방식</div>
        <div class="indent-1">가. <span class="var">{data.contract_method_sentence}</span></div>
        <div class="indent-1">나. <span class="var">적격심사 {data.qualification_ref}</span></div>
        <div class="indent-1">다. 청렴계약이행 서약제 대상입니다.</div>
        <div class="indent-1">라. 입찰서는 반드시 국가종합전자조달시스템(www.g2b.go.kr)의 전자입찰특별유의서에 따라 제출하여야 합니다.</div>
        <div style="margin: 5px 0 5px 40px; font-size: 10pt;">
            ※ 입찰 전 납품규격, 납품가능 금액, 납품가능 여부 등을 반드시 확인하시기를 바라며, 이에 대한 검토 없이 무리하게 저가 입찰한 책임은 입찰참가자에게 있음을 알려드립니다.<br>
            ※ 기타 세부사항은 전자입찰 공고서에 첨부된 규격서(시방서), 과업내용서 등을 반드시 확인하신 후 과업이행에 필요한 총금액을 산출하여 투찰하시기 바랍니다.
        </div>
        <div class="indent-1">마. 입찰금액은 반드시 부가가치세를 포함한 금액으로 제출하여야 하며 비영리법인 등 부가가치세 면제대상인 경우 견적금액에서 부가가치세를 차감한 금액을 계약금액으로 결정합니다.</div>
        <div class="indent-1">바. 정부입찰·계약집행기준 제10조의2 제2항제7호에 따라 전자입찰서 제출 후 정당한 이유없이 계약에 응하지 아니하거나 포기서를 제출하는 경우에는 나라장터 전자조달시스템에 수의계약배제업체로 등록되며, 등록일로부터 3개월간 공단과의 소액수의 계약이 제한됩니다.</div>

        <div class="section-title">3. 입찰참가자격 : 아래의 입찰참가자격을 모두 갖춘 자이어야 합니다.</div>

        {item_rows_html}
        
        {industry_rows_html}

        {direct_production_html}

        <div class="indent-1">나. 「{law["full_name"]}」 {law["부정당업자조항"]}(부정당업자의 입찰참가 자격제한)에 해당되지 아니한 업체</div>

        <div class="indent-1">
            다. 「{law["full_name"]}」 {law["조세포탈조항"]} 및 같은 법 시행령 {law["시행령_조세포탈"]}에 따라 '조세포탈 등을 한 자'로서 유죄판결이 확정된 날부터 2년이 지나지 아니한 자는 입찰에 참여할 수 없습니다.<br>
            입찰자는 같은 법 시행령 {law["시행령_조세포탈"]} 각 호에 해당하지 아니한다는 서약서를 입찰시 제출하여야 합니다. 만일 서약내용이 허위로 판명될 경우 계약의 해제·해지를 당할 수 있고, 부정당업자 입찰참가자격제한처분을 받을 수 있습니다.<br>
            다만, 나라장터 시스템을 이용하여 제출하는 경우에는 전자입찰서에 동 서약서의 내용을 포함하고 있으므로 전자입찰서 제출로 서약서 제출을 갈음합니다.
        </div>

        {restriction_detail_html}

        <div class="section-title">4. 공동계약</div>
        <div class="indent-1">
            <span class="var">{'본 계약은 공동수급을 허용합니다.' if data.joint_contract_allow else '본 계약은 공동수급을 허용하지 않습니다.'}</span>
        </div>

        <div class="section-title">5. 예정가격 및 낙찰자 결정방법</div>
        <div class="indent-1">가. 예정가격은 예비가격기초금액기준 ±2% 범위내에서 작성된 15개 복수 예비가격 중 입찰에 참여하는 각 업체가 추첨(2개씩 선택)한 번호 중 가장 많이 선택된 4개의 예비가격을 산술평균한 가격으로 결정됩니다.</div>
        <div class="indent-1">나. 낙찰자(계약상대자) 선정은 예정가격의 <span class="var">{data.winning_rate}%</span> 이상으로 견적서를 제출한 자 중 최저가격으로 견적서를 제출한 자 순서에 따라 「공직자의 이해충돌방지법」 제12조제1항 수의계약 체결 제한 사유에 해당하지 아니한 자를 계약상대자로 결정합니다.</div>
        <div class="indent-1">다. 낙찰이 될 수 있는 동일가격으로 견적 제출한 자가 2인 이상일 때에는 {law["short_name"]} 시행령 제47조 규정에 의거 낙찰자를 결정합니다. 전자입찰유의서 제15조에 따라 추첨에 의해 낙찰자를 결정하는 경우 전자조달시스템을 통한 자동추첨방식을 적용하여 계약상대자를 결정합니다.</div>

        <div class="section-title">6. 청렴계약이행 서약서 제출</div>
        <div class="indent-1">가. 입찰에 참여한 자는 모두 청렴계약이행을 위한 공정경쟁 및 청렴계약 입찰특별유의서 제3조에 의거 청렴계약이행서약서를 제출한 것으로 갈음합니다.</div>
        <div class="indent-2">· 우리공단은 청렴계약 실효성 확보를 위한 입찰담합방지책으로 손해배상제도를 시행하고 있으니 유의하여 주시기 바랍니다.</div>
        <div class="indent-2">· 관련자료는 한국환경공단 홈페이지(www.keco.or.kr) 입찰정보/집행기준에서 열람 및 다운 받을 수 있습니다.</div>

        <div class="section-title">7. 입찰보증금 납부 및 동 귀속</div>
        <div class="indent-1">가. 소액수의계약은 경쟁입찰이 아니므로 입찰보증금은 납부받지 아니합니다.</div>

        <div class="section-title">8. 입찰무효 또는 취소</div>
        <div class="indent-1">가. 「{law["시행령"]}」 {law["입찰무효조항_시행령"]}, 같은 법 시행규칙 {law["입찰무효조항_규칙"]} 및 「(계약예규){bid_doc}」 제12조에 해당되는 입찰은 무효입니다.</div>
        <div class="indent-1">나. 입찰참가자격등록증상의 상호 및 대표자(수인대표인 경우 대표자 전원의 성명을 모두 등재, 각자 대표도 해당)가 법인등기부등본상의 상호, 대표자와 다른 경우에는 입찰참가자격등록증을 변경등록하고 입찰에 참여하여야 하며, 변경등록하지 않고 참여한 입찰은 무효입찰임을 알려드립니다.</div>
        <div class="indent-1">다. 입찰참가자격의 판단기준일은 입찰참가자격등록 마감일(기준일이 정해져 있는 경우에는 해당일)이며 마감일까지 참가자격을 갖추지 않은 경우 무효입찰입니다.</div>
        <div class="indent-1">라. 「{law["시행규칙"]}」 {law["입찰무효조항_규칙"]} 및 「(계약예규){bid_doc}」 제12조에 정한 입찰무효 해당 여부 확인을 위하여 등록정보 확인을 위한 서류(법인등기부등본, 입찰대리인임을 증명하는 서류, 개인정보수집이용동의서 등)를 요청하는 경우, 낙찰대상자는 관계 서류를 제출하여야 합니다.</div>
        <div class="indent-1">마. 전자입찰의 취소 신청은 「국가종합전자조달시스템 전자입찰특별유의서」에 따라 전자입찰서 제출 마감시간 전까지 하셔야 하며, 취소 시 재입찰을 할 수 없습니다.</div>

        <div class="section-title">9. 하도급에 관한 사항</div>
        <div class="indent-1">가. 본 계약은 하도급 불가 건으로 개별 법령상 하도급 규정을 위반하여 하도급을 하거나, 발주기관 승인 없이 하도급을 하는 경우 부정당업자로 입찰참가자격 제한을 받을 수 있습니다.</div>

        <div class="section-title">10. 기타사항 및 추가정보 제공처</div>
        <div class="indent-1">가. 입찰에 참여하고자 하는 자는 공고서, 규격서, 과업내용서, 적격심사기준(적격심사 대상물품에 한함), {general_cond}, {special_cond}, {bid_doc}, 국가종합전자조달시스템 전자입찰특별유의서, 청렴계약 입찰특변유의서 및 이행각서 등 입찰에 필요한 모든 사항을 완전히 숙지하고 입찰에 참여하여야 하며, 이를 숙지하지 못하여 발생하는 책임은 입찰자에게 있습니다.</div>
        <div class="indent-1">나. 규격 착오 또는 규정의 미숙지 등으로 입찰자가 계약을 체결하지 않거나, 계약을 체결하고 불이행하는 경우 관계 법령에 따라 부정당업자로 제재되어 일정기간 입찰참여가 제한되는 등 불이익을 받으실 수 있으니, 본 입찰공고서의 규격서 및 계약관련 규정을 철저히 숙지하신 후 입찰에 참가하시기 바랍니다.</div>
        <div class="indent-1">다. 본 입찰은 국가종합전자조달시스템 전자입찰 특별유의서 제7조에 따른 신원확인 입찰이 적용되며, 개인인증서를 보유한 대표자 또는 입찰대리인은 국가종합전자조달시스템전자입찰특별유의서 제7조 제1항 제5호에 따라 미리 지문정보를 등록하여야 전자입찰서 제출이 가능합니다. 다만, 지문인식신원확인 입찰이 곤란한 자는 국가종합전자조달시스템 전자입찰특별유의서 제7조 제1항 제6호 및 제7호의 절차에 따라 예외적으로 개인인증서에 의한 전자입찰서 제출이 가능합니다.</div>
        <div class="indent-1">라. 기타 문의사항</div>
        <div class="indent-2">○ 전자입찰이용안내 : 국가종합전자조달시스템 콜센터(☎1588-0800)</div>
        <div class="indent-2">○ 물품 규격 등 관련사항 : <span class="var">{sec10_project}</span></div>
        <div class="indent-2">○ 입찰 계약 관련사항 : <span class="var">{sec10_contract}</span></div>

        <div class="integrity-box" style="margin-top: 30px;">
            <div class="integrity-title">&lt; 이의제기 및 신고채널 안내 &gt;</div>
            <div style="text-align: center;">
                ◎ 본 입찰과 관련한 부당행위 또는 부당사례 등과 공단 직원이 금품 및 향응요구, 지위남용 등 부당한 요구를 할 경우 아래 신고채널을 통해 신고할 수 있으며, 신고에 따른 일체의 불이익은 없습니다.<br><br>
                K-eco 신문고 공단홈페이지(www.keco.or.kr) > 국민참여 > K-eco신문고<br>
                - 부패신고센터 : 전화 032-590-3072 FAX 032-590-3069
            </div>
        </div>

        <div class="footer">
            위와 같이 공고합니다.<br><br>
            <span class="var">{today_str}</span><br><br>
            한국환경공단 계약담당
        </div>
        
    </body>
    </html>
    """
    return html.strip()


if __name__ == "__main__":
    # Test block
    from src.schema import PurchasePlan, PlannedNotice
    
    mock_plan = PurchasePlan(
        notice_name="2025년 토양폐기물분석부 시험분석 소모품 구매(단가계약) 계획(안)",
        budget_total=61104230,
        budget_supply=55549300,
        item_codes=["4111331501"],
        item_names=["시험분석 소모품"],
        industry_codes=["123456"],
        industry_names=["시험분석기기 제조업"],
        law_basis=["환경친화적 산업구조로의 전환촉진에 관한 법률"],
        law_article=["제1조"],
        contract_method_text="소액수의",
        delivery_period_text="계약일로부터 12개월",
        project_contact="032-123-4567",
        contract_contact="032-987-6543",
        # 4대 파라미터
        contract_law_type="국가계약법",
        contract_type="물품구매",
        winner_determination="소액수의",
        bidding_method="수의계약",  # 소액수의이므로 자동으로 수의계약
        bid_submission_start="2025-06-01 09:00",
        bid_submission_end="2025-06-05 10:00",
        bid_opening_datetime="2025-06-05 11:00"
    )
    mock_planned = PlannedNotice(
        notice_type="소액수의",
        sme_restriction="소기업·소상공인",
        submission_period="게시일로부터 3일간",
        contract_method_sentence="소액수의(견적입찰)",
        qualification_sentences=["소기업 확인서 소지자"],
        joint_contract_sentence="공동계약 불허",
        notice_name="2025년 토양폐기물분석부 시험분석 소모품 구매(단가계약)",
        budget_format="61,104,230원",
        project_contact="032-123-4567",
        contract_contact="032-987-6543",
        # 4대 파라미터
        contract_law_type="국가계약법",
        contract_type="물품구매",
        winner_determination="소액수의",
        bidding_method="수의계약"
    )
    
    result = write_notice(mock_plan, mock_planned)
    print(result)
