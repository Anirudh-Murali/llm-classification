import json
import logging
import aiohttp
from typing import Dict, Any
from .base import BaseLLMClient
from ..models.config import LLMConfig

logger = logging.getLogger(__name__)

class GeminiClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        if not self.config.api_key:
            raise ValueError("API Key is required for Gemini provider")
        
        # Default to gemini-pro if not specified
        if self.config.model is None:
            raise ValueError("Model is required for Gemini provider")
        model = self.config.model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.config.api_key}"

    async def aclassify(self, text: str, system_prompt: str, schema: Dict[str, Any] = None) -> Dict[str, Any]:
        # Construct prompt structure for Gemini
        # Gemini doesn't have a strict "system" role in the same way as OpenAI in v1beta always,
        # but we can prepend it or use the 'system_instruction' if the model supports it (Gemini 1.5).
        # For broad compatibility with 'gemini-pro', we'll prepend the system prompt to the user message
        # or use a multi-turn structure if needed. Simple prepending works well usually.
        
        full_prompt = f"{system_prompt}\n\nUser Input:\n{text}\n\nRespond in JSON."
        
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": self.config.temperature,
                "topP": self.config.top_p,
                "topK": self.config.top_k,
                "responseMimeType": "application/json" # Enforce JSON mode for newer models
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, timeout=self.config.timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API Error: {response.status} - {error_text}")
                        return {"category": "error", "reasoning": f"API Error: {response.status}"}
                    
                    data = await response.json()
                    
                    try:
                        # Extract text from response
                        # Structure: candidates[0].content.parts[0].text
                        candidates = data.get("candidates", [])
                        if not candidates:
                            return {"category": "error", "reasoning": "No candidates returned"}
                            
                        # Check for safety blocks
                        if candidates[0].get("finishReason") == "SAFETY":
                             return {"category": "filtered", "reasoning": "Safety filter triggered"}

                        response_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                        
                        # Clean markdown code blocks if present
                        if response_text.startswith("```json"):
                            response_text = response_text.replace("```json", "", 1)
                            if response_text.endswith("```"):
                                response_text = response_text[:-3]
                        elif response_text.startswith("```"):
                             response_text = response_text.replace("```", "", 1)
                             if response_text.endswith("```"):
                                response_text = response_text[:-3]
                                
                        result = json.loads(response_text)
                        return result
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode JSON response: {response_text}")
                        return {"category": "unclassified", "reasoning": "JSON Decode Error"}
                    except Exception as e:
                        logger.error(f"Error parsing Gemini response: {e}")
                        return {"category": "error", "reasoning": f"Parse Error: {e}"}

        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return {"category": "error", "reasoning": f"Request failed: {str(e)}"}
