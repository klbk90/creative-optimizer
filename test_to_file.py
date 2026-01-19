#!/usr/bin/env python3
import os
import anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

model = "claude-3-5-sonnet-20241022"

print("Testing model:", model)

try:
    response = client.messages.create(
        model=model,
        max_tokens=50,
        messages=[{"role": "user", "content": "Say hi in one word"}]
    )
    
    result = response.content[0].text
    
    with open("/tmp/claude_test_result.txt", "w", encoding="utf-8") as f:
        f.write(f"SUCCESS!\n")
        f.write(f"Model: {model}\n")
        f.write(f"Response: {result}\n")
    
    print("SUCCESS! Check result in: /tmp/claude_test_result.txt")
    
except Exception as e:
    with open("/tmp/claude_test_result.txt", "w", encoding="utf-8") as f:
        f.write(f"FAILED!\n")
        f.write(f"Error: {str(e)}\n")
    
    print("FAILED! Check error in: /tmp/claude_test_result.txt")
