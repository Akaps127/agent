import os
from fastmcp import FastMCP
from src.graph import app

# 1. MCP 서버 생성
mcp = FastMCP("Auto-Bid-Gen")

# 2. 도구 등록
@mcp.tool()
def generate_bid_notice(pdf_path: str) -> str:
    """
    주어진 PDF 구매계획서를 분석하여 입찰공고문(HTML)을 생성합니다.
    
    Args:
        pdf_path (str): 분석할 PDF 파일의 절대 경로 또는 상대 경로.
    """
    # 파일 존재 여부 확인
    if not os.path.exists(pdf_path):
        return f"❌ 에러: 파일을 찾을 수 없습니다. 경로를 확인해주세요: {pdf_path}"

    try:
        # LangGraph 실행
        print(f"🚀 공고문 생성 시작: {pdf_path}")
        result = app.invoke({"pdf_path": pdf_path})
        
        final_html = result.get("final_output", "")
        
        if not final_html:
            return "❌ 공고문 생성 실패: 결과값이 비어 있습니다."

        # 파일 저장 (덮어쓰기)
        output_file = "final_notice.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_html)
            
        # 결과 요약 반환
        return f"""
✅ **공고문 생성이 완료되었습니다!**

📂 **저장된 파일:** `{output_file}`
(이 파일을 MS Word로 열면 편집 가능합니다)

---
**[미리보기]**
{final_html[:500]}...
(이하 생략)
"""

    except Exception as e:
        return f"❌ 시스템 에러 발생: {str(e)}"

# 3. 서버 실행 (if main)
if __name__ == "__main__":
    mcp.run()
