import requests
import json
response = requests.get(
  url="https://openrouter.ai/api/v1/auth/key",
  headers={
    "Authorization": f"Bearer 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"
  }
)
print(json.dumps(response.json(), indent=2))