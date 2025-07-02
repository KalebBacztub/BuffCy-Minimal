# prompts.py

# This system prompt gives the LLM its persona and overall context.
SYSTEM_PROMPT = """
You are BuffCy, an expert AI agent specializing in autonomous vulnerability research and exploitation. 
Your specific mission is to analyze the state of a crashed program under GDB to find memory corruption vulnerabilities.
You will be given specific tasks and GDB output. Your analysis must be precise, accurate, and your responses must be in the exact format requested.
"""

# This prompt template is for the offset calculation task.
FIND_OFFSET_PROMPT = """
A target program has been crashed with a unique cyclic pattern of {pattern_length} bytes.
The GDB output shows the following register state at the time of the crash:
--- GDB DUMP ---
{gdb_output}
--- END DUMP ---

Analyze this data to determine the EIP register's value. Based on that value, calculate the exact offset in bytes to overwrite the EIP.

Provide ONLY the final integer offset as your answer.
"""

# This prompt template is for selecting a return address.
SELECT_RETURN_ADDRESS_PROMPT = """
The program has been crashed and we have control of EIP. The stack pointer (ESP) is at {esp_value}.
We are injecting a payload that includes a 200-byte NOP sled (`\\x90`).
Select an ideal return address that will land execution within the NOP sled. A good address is typically a short distance (e.g., 20-50 bytes) into the sled from the start of our controlled buffer, which is near the ESP.
The goal is reliability. Choose a clear address from the provided stack dump.

--- STACK DUMP NEAR ESP ---
{stack_dump}
--- END DUMP ---

Provide ONLY the chosen hexadecimal address as your answer (e.g., 0xbfffe298).
"""