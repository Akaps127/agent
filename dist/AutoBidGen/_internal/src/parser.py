"""
PDF/HWP 파서 모듈 - Claude를 사용한 조달 문서 분석

PDF 또는 HWP에서 텍스트를 추출하고 Claude를 사용하여 구매계획 데이터를 파싱합니다.
추출된 세부품명번호를 나라장터 API로 조회하여 물품명을 가져옵니다.
"""

import re
import os
import pdfplumber
import zlib
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.schema import PurchasePlan
from src.g2b_api import get_product_names
from src.industry_api import get_industry_infos
from src.direct_production_api import get_direct_production_clauses
from src.config import settings


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF 파일에서 텍스트 추출"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""
    return text


def extract_text_from_hwp(hwp_path: str) -> str:
    """
    HWP 파일에서 텍스트 추출 (olefile 사용)
    HWP 파일은 OLE2 형식으로 저장되며, PrvText 또는 BodyText 스트림에서 텍스트 추출
    """
    text = ""
    try:
        import olefile
    except ImportError:
        print("[ERROR] olefile library not installed")
        return ""
    
    # HWP 파일이 OLE 형식인지 확인
    if not olefile.isOleFile(hwp_path):
        print(f"[WARN] File is not OLE format (may be HWPX): {hwp_path}")
        # HWPX 형식 시도 (ZIP 기반)
        try:
            import zipfile
            with zipfile.ZipFile(hwp_path, 'r') as zf:
                # HWPX는 Contents/section0.xml 등에 텍스트 포함
                for name in zf.namelist():
                    if 'section' in name.lower() and name.endswith('.xml'):
                        content = zf.read(name).decode('utf-8', errors='ignore')
                        # XML 태그 제거
                        text += re.sub(r'<[^>]+>', '', content) + "\n"
                if text.strip():
                    print(f"[HWPX] Extracted {len(text)} chars from HWPX")
                    return text
        except Exception as e:
            print(f"[WARN] HWPX extraction failed: {e}")
        return ""
    
    try:
        ole = olefile.OleFileIO(hwp_path)
        
        # 방법 1: PrvText 스트림에서 미리보기 텍스트 추출
        if ole.exists("PrvText"):
            try:
                prv_text_data = ole.openstream("PrvText").read()
                text = prv_text_data.decode("utf-16-le", errors="ignore")
                text = text.replace("\x00", "")
                print(f"[HWP] Extracted {len(text)} chars from PrvText stream")
            except Exception as e:
                print(f"[HWP] PrvText extraction failed: {e}")
        
        # 방법 2: PrvText가 없거나 비어있으면 BodyText에서 추출
        if not text.strip():
            body_sections = [s for s in ole.listdir() if s[0] == "BodyText"]
            
            for section in body_sections:
                try:
                    stream_path = "/".join(section)
                    data = ole.openstream(stream_path).read()
                    
                    try:
                        decompressed = zlib.decompress(data, -15)
                        section_text = decompressed.decode("utf-16-le", errors="ignore")
                        section_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', section_text)
                        text += section_text + "\n"
                    except zlib.error:
                        section_text = data.decode("utf-16-le", errors="ignore")
                        section_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', section_text)
                        text += section_text + "\n"
                except Exception as e:
                    print(f"[HWP] BodyText section extraction failed: {e}")
                    continue
            
            if text.strip():
                print(f"[HWP] Extracted {len(text)} chars from BodyText stream")
        
        ole.close()
        
        if not text.strip():
            print(f"[WARN] No text extracted from HWP file")
            
    except Exception as e:
        print(f"[ERROR] HWP extraction failed: {e}")
        return ""
    
    return text



def extract_text(file_path: str) -> str:
    """
    파일 확장자에 따라 적절한 텍스트 추출 방법 선택
    - .pdf: pdfplumber 사용
    - .hwp: olefile 사용
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".hwp":
        return extract_text_from_hwp(file_path)
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")



def extract_item_codes_regex(text: str) -> list[str]:
    """
    정규식으로 PDF 텍스트에서 모든 유효한 10자리 세부품명번호 추출
    - 날짜 형식(2024, 2025 등으로 시작)은 제외
    - 중복 제거
    """
    
    def is_valid_item_code(code: str) -> bool:
        """유효한 세부품명번호인지 검증"""
        if not code or len(code) != 10:
            return False
        # 날짜 형식 제외 (2020~2030으로 시작하는 경우)
        if code.startswith(('2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027', '2028', '2029', '2030')):
            return False
        # 0으로 시작하는 경우도 일반적으로 세부품명번호가 아님
        if code.startswith('0'):
            return False
        return True
    
    results = []
    
    # 방법 1: "세부품명번호" 또는 "품명번호" 라벨 근처에서 모두 찾기
    label_pattern = r'(?:세부품명번호|품명번호|물품분류번호|분류번호)[^\d]*(\d{10})'
    label_matches = re.findall(label_pattern, text)
    for code in label_matches:
        if is_valid_item_code(code) and code not in results:
            print(f"  [OK] Found item code near label: {code}")
            results.append(code)
    
    # 방법 2: 모든 유효한 10자리 숫자 찾기
    pattern_exact = r'\b(\d{10})\b'
    found_exact = re.findall(pattern_exact, text)
    
    for code in found_exact:
        if is_valid_item_code(code) and code not in results:
            print(f"  [OK] Found valid 10-digit code: {code}")
            results.append(code)
    
    if not results:
        print(f"  [WARN] No valid 10-digit item code found")
    else:
        print(f"  [INFO] Total {len(results)} item codes found")
    
    return results


def extract_industry_codes_regex(text: str) -> list[str]:
    """
    정규식으로 PDF 텍스트에서 업종코드 추출
    - 패턴 A: "업종코드" 바로 다음 숫자 (신뢰도 95%)
    - 패턴 B: 괄호 안 패턴 (업종코드 XXXX) (신뢰도 90%)
    - 패턴 C: "업종코드" 앞뒤 50자 내 가장 가까운 3~6자리 숫자 (신뢰도 75%)
    """
    
    def is_valid_code(code: str) -> bool:
        """유효한 업종코드인지 검증"""
        if not code or len(code) < 3 or len(code) > 6:
            return False
        # 날짜 형식 제외 (2020~2030으로 시작하는 경우)
        if code.startswith(('2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027', '2028', '2029', '2030')):
            return False
        return True
    
    results = []
    keyword = "업종코드"
    
    # "업종코드" 키워드의 모든 위치 찾기
    for match in re.finditer(keyword, text):
        start_pos = match.start()
        end_pos = match.end()
        
        # 주변 ±120자 추출
        context_start = max(0, start_pos - 120)
        context_end = min(len(text), end_pos + 120)
        context = text[context_start:context_end]
        
        # 패턴 A: "업종코드" 바로 다음 숫자 (최고 우선순위)
        pattern_a = r'업종코드\s*[:：]?\s*(\d{3,6})'
        match_a = re.search(pattern_a, context)
        if match_a:
            code = match_a.group(1)
            if is_valid_code(code) and code not in results:
                print(f"  [OK] Found industry code (pattern A - direct): {code}")
                results.append(code)
                continue
        
        # 패턴 B: 괄호 안 패턴 (업종코드 XXXX)
        pattern_b = r'\(.*?업종코드\s*[:：]?\s*(\d{3,6}).*?\)'
        match_b = re.search(pattern_b, context)
        if match_b:
            code = match_b.group(1)
            if is_valid_code(code) and code not in results:
                print(f"  [OK] Found industry code (pattern B - parentheses): {code}")
                results.append(code)
                continue
        
        # 패턴 C: "업종코드" 앞뒤 50자 내 가장 가까운 3~6자리 숫자
        context_short = text[max(0, start_pos - 50):min(len(text), end_pos + 50)]
        numbers = re.findall(r'\b(\d{3,6})\b', context_short)
        
        if numbers:
            # 가장 가까운 숫자 찾기
            closest_code = None
            min_distance = float('inf')
            
            for num in numbers:
                if is_valid_code(num):
                    # 업종코드와의 거리 계산
                    num_pos = context_short.find(num)
                    keyword_pos = context_short.find(keyword)
                    distance = abs(num_pos - keyword_pos)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_code = num
            
            if closest_code and closest_code not in results:
                print(f"  [OK] Found industry code (pattern C - nearby): {closest_code}")
                results.append(closest_code)
    
    if not results:
        print(f"  [INFO] No industry code found with any pattern")
    
    return results


def parse_document(file_path: str) -> PurchasePlan:
    """
    PDF 또는 HWP 파일을 파싱하여 PurchasePlan 객체로 반환
    1. 문서 텍스트 추출 (PDF/HWP 자동 감지)
    2. Claude로 데이터 파싱
    3. 정규식으로 세부품명번호 추출 (Claude 보완)
    4. 나라장터 API로 물품명 조회
    """
    # 파일 확장자로 문서 타입 확인
    ext = os.path.splitext(file_path)[1].lower()
    doc_type = "HWP" if ext == ".hwp" else "PDF"
    
    # 1. Extract text
    text = extract_text(file_path)
    if not text:
        raise ValueError(f"Failed to extract text from {file_path}")
    
    print(f"[{doc_type}] Text extracted: {len(text)} chars")

    # 2. Setup Claude LLM
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in environment variables.")

    llm = ChatAnthropic(
        model=settings.claude_model,
        temperature=0,
        anthropic_api_key=settings.anthropic_api_key,
        max_tokens=4096
    )
    
    print(f"[LLM] Using Claude model: {settings.claude_model}")

    # 3. Setup Parser & Prompt
    parser = PydanticOutputParser(pydantic_object=PurchasePlan)

    system_prompt = """너는 조달 데이터 전문가다. 
주어진 구매계획안(또는 입찰공고문) 텍스트에서 데이터를 추출하여 정해진 형식으로 반환하라.

**중요 로직:**
1. 문서에 공급가액(VAT 제외)이 명시되지 않았다면, `budget_total` (소요예산, 부가세 포함) 값을 1.1로 나누어 계산하고 정수로 반올림하여 `budget_supply`에 넣어라.
   - 즉, `budget_supply = round(budget_total / 1.1)`

2. **세부품명번호 추출 (매우 중요):**
   - `item_codes`는 문서에 있는 모든 10자리 숫자를 찾아 리스트로 반환하라.
   - 10자리 숫자는 "세부품명번호", "품명번호", "물품분류번호", "분류번호" 등의 라벨 근처에 있을 수 있다.
   - 표(table) 형식으로 되어있다면 각 행마다 하나씩 있을 수 있다.
   - 예: "4111331501", "4612220601", "4612220101" 등
   - 문서에서 발견되는 모든 10자리 코드를 빠짐없이 추출하라.
   - 만약 10자리 숫자를 찾을 수 없다면 빈 리스트 []를 반환하라. 절대 추측하지 마라.

3. **물품명 추출:**
   - `item_names`는 문서에 명시된 물품명/품명을 리스트로 반환하라.
   - item_codes가 있다면 순서를 일치시켜라.

4. `contract_method_text`는 문서에 적힌 그대로 추출하라.
5. 지역 관련 제한 문구가 있다면 `region_restriction_text`에, 중소기업/소상공인 관련 문구가 있다면 `sme_restriction_text`에 넣어라.

출력은 반드시 올바른 JSON 형식을 따라야 한다.
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "다음 텍스트를 분석해줘:\n\n{text}\n\n{format_instructions}")
    ])

    chain = prompt | llm | parser

    # 4. Invoke Chain
    try:
        print("[LLM] Starting Claude chain...")
        result = chain.invoke({
            "text": text,
            "format_instructions": parser.get_format_instructions()
        })
        print("[LLM] Claude chain completed")
        
        print(f"[LLM] Claude extracted item_codes: {result.item_codes} (will be ignored)")
        print(f"[LLM] Claude extracted item_names: {result.item_names}")
        
    except Exception as e:
        print(f"[ERROR] Claude invocation failed: {e}")
        # Claude 실패 시 기본 객체 생성 시도 (빈 값들)
        try:
            # PurchasePlan is already imported at top of file
            result = PurchasePlan(
                notice_name="Extraction Failed",
                budget_total=0,
                budget_supply=0,
                contract_method_text="Extraction Failed"
            )
            print("[WARN] Created default PurchasePlan due to Claude failure")
        except Exception as e2:
            print(f"[ERROR] Default object creation also failed: {e2}")
            raise e

    # 5. 정규식으로 10자리 연속 숫자 추출 (핵심 - Claude 결과 무시)
    try:
        print("[REGEX] Starting regex extraction...")
        regex_codes = extract_item_codes_regex(text)
        print(f"[REGEX] Found {len(regex_codes)} 10-digit codes: {regex_codes}")
        
        # Claude의 item_codes는 무시하고, 정규식 결과만 사용
        result = result.model_copy(update={"item_codes": regex_codes})
    except Exception as e:
        print(f"[ERROR] Regex extraction failed: {e}")
        regex_codes = []

    # 6. 나라장터 API로 물품명 조회
    try:
        if regex_codes:
            print(f"[API] Looking up {len(regex_codes)} item codes...")
            g2b_product_names = get_product_names(regex_codes)
            
            final_codes = []
            final_names = []
            
            for code in regex_codes:
                final_codes.append(code)
                api_name = g2b_product_names.get(code)
                if api_name:
                    final_names.append(api_name)
                else:
                    final_names.append(f"Unknown ({code})")
            
            result = result.model_copy(update={
                "item_codes": final_codes,
                "item_names": final_names
            })
            print(f"[DONE] Item codes extraction complete")
        else:
            result = result.model_copy(update={"item_codes": [], "item_names": []})
            print(f"[WARN] No 10-digit codes found in document.")
    except Exception as e:
        print(f"[ERROR] API lookup failed: {e}")
    
    # 7. 정규식으로 업종코드 추출
    try:
        print("[REGEX] Extracting industry codes...")
        regex_industry_codes = extract_industry_codes_regex(text)
        if regex_industry_codes:
            result = result.model_copy(update={"industry_codes": regex_industry_codes})
            print(f"[REGEX] Found industry codes: {regex_industry_codes}")
    except Exception as e:
        print(f"[ERROR] Industry code regex extraction failed: {e}")
    
    # 8. 업종 API로 업종명, 근거법령, 법령조항 조회
    try:
        industry_codes = result.industry_codes or []
        if industry_codes:
            print(f"[Industry API] Looking up {len(industry_codes)} industry codes...")
            industry_infos = get_industry_infos(industry_codes)
            
            final_industry_names = []
            final_law_basis = []
            final_law_article = []
            
            for code in industry_codes:
                info = industry_infos.get(code, {})
                final_industry_names.append(info.get("industry_name", ""))
                final_law_basis.append(info.get("law_basis", ""))
                final_law_article.append(info.get("law_article", ""))
            
            result = result.model_copy(update={
                "industry_names": final_industry_names,
                "law_basis": final_law_basis,
                "law_article": final_law_article
            })
            print(f"[DONE] Industry info extraction complete")
    except Exception as e:
        print(f"[ERROR] Industry API lookup failed: {e}")
    
    # 9. 직접생산확인증명서 조항 생성
    try:
        item_codes = result.item_codes or []
        item_names = result.item_names or []
        if item_codes and item_names:
            print(f"[DirectProd API] Checking {len(item_codes)} items for direct production...")
            clauses = get_direct_production_clauses(item_codes, item_names)
            if clauses:
                result = result.model_copy(update={"direct_production_clauses": clauses})
                print(f"[DONE] Found {len(clauses)} direct production clauses")
    except Exception as e:
        print(f"[ERROR] Direct production API failed: {e}")
    
    return result


if __name__ == "__main__":
    from pprint import pprint
    import os
    
    # 테스트 파일 경로 (PDF 또는 HWP)
    test_file = "구매계획안소액 2.pdf" 
    
    if os.path.exists(test_file):
        result = parse_document(test_file)
        print("\n--- [JSON Result] ---")
        pprint(result.model_dump())
    else:
        print(f"File not found: {test_file}")
