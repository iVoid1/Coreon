import aiohttp, requests
from BitVoid.config.Config import config


class OllamaModel:
    def __init__(self):
        self.model_name = config.OLLAMA_MODEL

    def chat(self, prompt: str) -> str | None:
        """Send a basic synchronous chat request (non-streamed)."""
        if not prompt.strip():
            print("Prompt is empty. Please provide a valid input.")
            return None

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            response = requests.post("http://localhost:11434/api/chat", json=payload)
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                return None

            data = response.json()
            return data.get("message", {}).get("content")

        except requests.RequestException as e:
            print(f"Ollama connection error: {e}")
            return None

    async def ask_ollama(self, prompt: str) -> str | None:
        """Send an asynchronous chat request (non-streamed)."""
        # TODO: Add streaming support later if needed
        if not prompt.strip():
            print("Prompt is empty. Please provide a valid input.")
            return None

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://localhost:11434/api/chat", json=payload) as response:
                    if response.status != 200:
                        print(f"Error: {response.status} - {await response.text()}")
                        return None

                    data = await response.json()
                    return data.get("message", {}).get("content")

        except aiohttp.ClientError as e:
            print(f"Ollama (async) connection error: {e}")
            return None

    # TODO: Implement streaming support if needed
    # TODO: Add message memory if planning conversation history
