from typing import Optional, Dict, Any
from pydantic import BaseModel

class GrievanceRow(BaseModel):
    row_index: int
    comment: str
    original_data: Dict[str, Any]
    category: Optional[str] = None
    reasoning: Optional[str] = None
    language: Optional[str] = None
    translation: Optional[str] = None
