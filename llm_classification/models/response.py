from typing import Optional, Literal
from pydantic import BaseModel, Field

class ClassificationResponse(BaseModel):
    language: Literal["en", "mr", "hi"] = Field(description="Detected language code")
    translation: Optional[str] = Field(default=None, description="English translation if not English")
    category: str = Field(description="The classification category")
    reasoning: str = Field(description="Explanation for the classification")
