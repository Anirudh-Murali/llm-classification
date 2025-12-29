# LLM Clients

This module contains LLM client implementations for different providers.

## Architecture

All LLM clients inherit from `BaseLLMClient` abstract class and implement the `aclassify()` async method.

## Current Implementations

### OllamaClient
- **File**: `ollama.py`
- **Provider**: Ollama (local LLM server)
- **Features**: Async requests, JSON mode, configurable timeout

## Adding New Providers

To add support for a new LLM provider (e.g., OpenAI, Gemini, Groq):

1. Create a new file: `llm_clients/<provider_name>.py`
2. Import the base class: `from .base import BaseLLMClient`
3. Create your client class inheriting from `BaseLLMClient`
4. Implement the `aclassify(self, text: str, system_prompt: str) -> Dict[str, Any]` method
5. Return a dict with `{"category": "...", "reasoning": "..."}`

### Example Template

```python
from typing import Dict, Any
from .base import BaseLLMClient
from ..models.config import LLMConfig

class NewProviderClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        # Initialize your client here
    
    async def aclassify(self, text: str, system_prompt: str) -> Dict[str, Any]:
        # Your implementation here
        # Make async API call
        # Parse response
        return {
            "category": "category_name",
            "reasoning": "why this category was chosen"
        }
```

6. Update `orchestrator.py` to support the new provider in `_get_llm_client()` method
7. Update `config.yaml` to add provider-specific settings if needed

## Configuration

Each client receives an `LLMConfig` object with:
- `provider`: Provider name
- `model`: Model identifier
- `base_url`: API endpoint (if applicable)
- `max_concurrency`: Concurrency limit
- `timeout`: Request timeout in seconds
