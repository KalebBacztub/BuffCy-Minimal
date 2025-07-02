# agent.py
import os
from openai import OpenAI
import re
import json
from prompts import SYSTEM_PROMPT, FIND_OFFSET_PROMPT

class ExploitAgent:
    # ... (_call_llm and generate_cyclic_pattern remain the same) ...
    def __init__(self, model_name="openai/gpt-4o"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key: raise ValueError("OPENROUTER_API_KEY not found in .env file.")
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        self.model = model_name

    def _call_llm(self, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            raw_response_content = response.choices[0].message.content
            print("\n--- [AI REASONING] ---")
            print(raw_response_content)
            print("--- [END AI REASONING] ---\n")
            return raw_response_content
        except Exception as e:
            print(f"LLM Error: {e}")
            return f"LLM Error: {e}"

    def generate_cyclic_pattern(self, length: int) -> str:
        charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        pattern = ""
        for i in range(length // 3):
            c1 = charset[(i // (len(charset) * len(charset))) % len(charset)]
            c2 = charset[(i // len(charset)) % len(charset)]
            c3 = charset[i % len(charset)]
            pattern += c1 + c2 + c3
        return pattern[:length]

    def analyze_crash_and_get_offset(self, crash_data: dict, pattern_length: int) -> int:
        prompt = FIND_OFFSET_PROMPT.format(
            pattern_length=pattern_length,
            gdb_output=json.dumps(crash_data, indent=2)
        )
        response_text = self._call_llm(prompt)
        match = re.search(r'\d+', response_text)
        if match:
            return int(match.group(0))
        raise ValueError("LLM response did not contain a valid integer offset.")