from typing import List
from typing import Optional, Literal
from pydantic import BaseModel, Field

class ClassificationResponse(BaseModel):
    id: str = Field(description="The unique identifier provided in the input (e.g., TicketNumber)")
    language: Literal["en", "mr", "hi"] = Field(description="Detected language code")
    translation: str = Field(description="English translation of the comment (copy original if already English)")
    reasoning: str = Field(description="Explanation for the classification")
    category: str = Field(description="The classification category")

class BatchClassificationResponse(BaseModel):
    results: List[ClassificationResponse] = Field(description="List of classification results corresponding to the input comments")
