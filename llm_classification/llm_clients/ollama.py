import json
import logging
import aiohttp
from typing import Dict, Any
from .base import BaseLLMClient
from ..models.config import LLMConfig

logger = logging.getLogger(__name__)

class OllamaClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_url = f"{config.base_url.rstrip('/')}/api/generate"

    async def aclassify(self, text: str, system_prompt: str) -> Dict[str, Any]:
        prompt = f"Comment: {text}\n\nClassify this comment."
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, timeout=self.config.timeout) as response:
                    if response.status != 200:
                        logger.error(f"Ollama API Error: {response.status} - {await response.text()}")
                        return {"category": "error", "reasoning": f"API Error: {response.status}"}
                    
                    data = await response.json()
                    response_text = data.get("response", "{}")
                    
                    try:
                        result = json.loads(response_text)
                        # Normalize keys
                        return {
                            "category": result.get("category", "unclassified"),
                            "reasoning": result.get("reasoning", "")
                        }
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode JSON response: {response_text}")
                        return {"category": "unclassified", "reasoning": "JSON Decode Error"}

        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return {"category": "error", "reasoning": f"Request failed: {str(e)}"}
