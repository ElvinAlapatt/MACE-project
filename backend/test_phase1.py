# backend/test_phase1.py

# backend/test_phase2.py

from app.engine.graph import mace_graph

def test_mace(task: str):
    print("\n" + "="*60)
    print("🚀 MACE Phase 2 Test — Coder + QA Loop")
    print("="*60)
    print(f"Task: {task}\n")
    
    result = mace_graph.invoke({
        "user_request": task,
        "generated_code": "",
        "messages": [],
        "qa_feedback": "",
        "qa_status": "",
        "test_results": "",
        "retry_count": 0,
        "max_retries": 3        # QA can bounce code back up to 3 times
    })
    
    print("\n" + "="*60)
    print("📋 FINAL REPORT")
    print("="*60)
    print(f"Status:       {result['qa_status'].upper()}")
    print(f"Retry count:  {result['retry_count']}")
    print(f"\n📄 Final Code:\n{result['generated_code']}")
    print(f"\n🔍 QA Feedback:\n{result['qa_feedback']}")
    
    return result

if __name__ == "__main__":
    # Test 1: Something that should pass first try
    test_mace("""
Write a Python script that:
1. Imports a module called 'dataforge'
2. Uses dataforge.transform() to process a list [1,2,3,4,5]
3. Prints the result
""")

    # Test 2: Try something more complex
    # test_mace("Write a function that finds the fibonacci sequence up to n terms")
