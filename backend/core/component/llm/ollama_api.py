import aiohttp
import json


class Client:
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def generate(self, prompt: str | list, max_tokens: int = 512, temperature: float = 0.7):
        if isinstance(prompt, list):
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": prompt,
                "stream": True,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
        else:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                while True:
                    line = await response.content.readline()
                    if not line:
                        break
                    if line:
                        body = json.loads(line)
                        if isinstance(prompt, list):
                            token = body.get("message", {}).get("content", "")
                        else:
                            token = body.get("response", "")
                        yield token
                        if body.get("done", False):
                            break
