# test_phase3.py
import httpx
from app.engine.graph import mace_graph
import json

def check_ollama():
    try:
        httpx.get("http://localhost:11434")
        print("✅ Ollama is running\n")
    except:
        pass  # Groq mode doesn't need Ollama

def test_mace(task: str):
    print("\n" + "="*60)
    print("🚀 MACE Phase 3 Test — Full Pipeline")
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
        "max_retries": 3,
        "documentation": ""       # ← new field
    })

    print("\n" + "="*60)
    print("📋 FINAL REPORT")
    print("="*60)
    print(f"Status:      {result['qa_status'].upper()}")
    print(f"Retries:     {result['retry_count']}")
    print(f"\n📄 Final Code:\n{result['generated_code']}")
    print(f"\n📚 Documentation:\n{result['documentation']}")

    return result

if __name__ == "__main__":
    test_mace("Write a function that checks if a string is a palindrome")