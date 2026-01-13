from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END

# 각 모듈 임포트
from src.parser import parse_pdf
from src.nodes.planner import plan_notice
from src.nodes.writer import write_notice
from src.schema import PurchasePlan, PlannedNotice

# 1. 상태(State) 정의
class AgentState(TypedDict):
    pdf_path: str                  # 입력: PDF 파일 경로
    purchase_plan: Optional[PurchasePlan]    # Step 1 결과: 파싱된 데이터
    planned_notice: Optional[PlannedNotice]  # Step 2 결과: 기획된 공고 데이터
    final_output: Optional[str]              # Step 3 결과: 최종 HTML 공고문

# 2. 노드(Node) 함수 정의
def parser_node(state: AgentState):
    print(f"\n🚀 [Step 1] Parser 동작 중... ({state['pdf_path']})")
    try:
        # 실제 구현된 parse_pdf 함수 호출
        purchase_plan = parse_pdf(state['pdf_path'])
        return {"purchase_plan": purchase_plan}
    except Exception as e:
        print(f"❌ Parser 에러: {e}")
        # 에러 시 None 반환
        return {"purchase_plan": None}

def planner_node(state: AgentState):
    print("\n🧠 [Step 2] Planner 동작 중...")
    if not state.get('purchase_plan'):
        print("⚠️ 파싱 데이터 없음. 중단합니다.")
        return {"planned_notice": None}
        
    try:
        planned = plan_notice(state['purchase_plan'])
        return {"planned_notice": planned}
    except Exception as e:
        print(f"❌ Planner 에러: {e}")
        return {"planned_notice": None}

def writer_node(state: AgentState):
    print("\n✍️ [Step 3] Writer 동작 중...")
    if not state.get('planned_notice'):
        return {"final_output": "에러: 공고 기획 데이터가 없습니다."}

    try:
        final_html = write_notice(state['purchase_plan'], state['planned_notice'])
        return {"final_output": final_html}
    except Exception as e:
        print(f"❌ Writer 에러: {e}")
        return {"final_output": f"에러 발생: {e}"}

# 3. 그래프(Graph) 조립
workflow = StateGraph(AgentState)

# 노드 등록
workflow.add_node("parser", parser_node)
workflow.add_node("planner", planner_node)
workflow.add_node("writer", writer_node)

# 엣지 연결 (순차 실행)
workflow.set_entry_point("parser")
workflow.add_edge("parser", "planner")
workflow.add_edge("planner", "writer")
workflow.add_edge("writer", END)

# 컴파일
app = workflow.compile()

if __name__ == "__main__":
    import os
    
    pdf_file = "구매계획안소액 2.pdf"
    if os.path.exists(pdf_file):
        print(f"--- [Graph 실행 테스트: {pdf_file}] ---")
        inputs = {"pdf_path": pdf_file}
        # invoke returns the final state
        result = app.invoke(inputs)
        
        final_out = result.get("final_output", "")
        if final_out and "<h1>" in final_out:
            print("\n✅ [Pass] 최종 결과물 생성 성공")
            print("--- [Preview] ---")
            print(final_out[:500])
        else:
            print(f"\n❌ [Fail] 최종 결과물 생성 실패: {final_out}")
            
        # [시각화 코드 추가]
        print("\n📊 그래프 시각화 파일 생성 중...")
        try:
            # Mermaid 형식의 PNG 이미지 데이터 생성
            png_data = app.get_graph().draw_mermaid_png()
            
            # 파일로 저장
            with open("graph_visualization.png", "wb") as f:
                f.write(png_data)
            print("✅ 'graph_visualization.png' 파일이 저장되었습니다!")
            
        except Exception as e:
            print(f"❌ 시각화 저장 실패: {e}")
            print("Tip: 'pip install grandalf' 또는 'pip install pygraphviz'가 필요할 수 있습니다.")

    else:
        print(f"File not found: {pdf_file}")
