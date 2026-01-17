#!/usr/bin/env python3
"""Test which Claude models are available with current API key."""
import os
import anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not set")
    exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Models to test (from newest to oldest)
models = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]

print("Testing Claude models with your API key...\n")

working_model = None
for model in models:
    try:
        print(f"Testing: {model}...", end=" ")
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print("✅ WORKS!")
        if not working_model:
            working_model = model
            print(f"   → First working model found: {model}")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not_found" in error_msg:
            print("❌ 404 Not Found")
        elif "401" in error_msg:
            print("❌ 401 Unauthorized")
        else:
            print(f"❌ Error: {error_msg[:50]}")

print("\n" + "="*60)
if working_model:
    print(f"✅ USE THIS MODEL: {working_model}")
else:
    print("❌ No working models found! Check API key permissions.")
print("="*60)
