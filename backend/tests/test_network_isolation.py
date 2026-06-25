from app.engine.utils import run_code_safely

code = '''
import urllib.request
urllib.request.urlopen("http://example.com", timeout=3)
print("NETWORK WORKED - THIS IS BAD")
'''

result = run_code_safely(code)
print(result)