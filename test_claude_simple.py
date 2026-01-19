#!/usr/bin/env python3
import os
import anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

models = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620", 
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
]

print("Testing Claude API models...")
print()

for model in models:
    try:
        print(f"Testing: {model}")
        response = client.messages.create(
            model=model,
            max_tokens=20,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"SUCCESS! Model works: {model}")
        print(f"Response: {response.content[0].text}")
        print()
        print("="*60)
        print(f"USE THIS MODEL: {model}")
        print("="*60)
        break
    except Exception as e:
        if "404" in str(e):
            print(f"  404 - not found")
        else:
            print(f"  Error: {str(e)[:100]}")
        print()
