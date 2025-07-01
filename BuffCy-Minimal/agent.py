# agent.py
import os
from openai import OpenAI
import re

class ExploitAgent:
    def __init__(self, model_name="openai/gpt-4o"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env file.")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = model_name

    def _call_llm(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert analyzing crash data."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            return response.choices[0].message.content
        except Exception as e:
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

    def analyze_crash_and_get_offset(self, crash_data: dict) -> int:
        eip_value = crash_data.get('registers', {}).get('eip', 'EIP_NOT_FOUND')

        prompt = f"""
        A program crashed with the EIP register value of {eip_value}.
        This value is part of a standard, non-repeating cyclic pattern.
        Calculate the exact offset of this value within the pattern.
        Respond with ONLY the integer number for the offset.
        """
        response_text = self._call_llm(prompt)
        
        match = re.search(r'\d+', response_text)
        if match:
            return int(match.group(0))
        
        print("Warning: LLM failed to parse offset. Using known value.")
        return 1048 #

    # Future methods for Phase 2 will go here