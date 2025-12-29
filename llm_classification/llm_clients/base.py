import abc
from typing import Dict, Any

class BaseLLMClient(abc.ABC):
    @abc.abstractmethod
    async def aclassify(self, text: str, system_prompt: str) -> Dict[str, Any]:
        """
        Classifies the text based on the system prompt asynchronously.
        Returns a dictionary with 'category' and 'reasoning'.
        """
        pass
