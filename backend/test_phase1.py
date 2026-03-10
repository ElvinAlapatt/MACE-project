# backend/test_phase1.py

# backend/test_phase2.py

from app.engine.graph import mace_graph
import httpx

def check_ollama():
    try:
        response = httpx.get("http://localhost:11434")
        print("✅ Ollama is running\n")
    except httpx.ConnectError:
        print("❌ Ollama is not running!")
        print("   Start it from: Start Menu → Ollama")
        print("   Or run: ollama serve")
        exit(1)

# Call it before anything else
check_ollama()
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
    # Should pass first try
    test_mace("Write a function that reverses a string")

    # Should fail once then pass
    test_mace("""Write a class called BankAccount with deposit, 
    withdraw, get_balance methods. Withdraw must raise ValueError 
    if amount exceeds balance. Demo all methods at the bottom.""")

    # Should detect IMPOSSIBLE early
    test_mace("""Write a Python script that imports dataforge 
    and uses dataforge.transform() on [1,2,3,4,5]""")

    # Test 2: Try something more complex
    # test_mace("Write a function that finds the fibonacci sequence up to n terms")
