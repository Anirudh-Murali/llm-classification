from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    provider: str
    model: str
    base_url: str
    max_concurrency: int = 5
    timeout: int = 60
    temperature: float = 0.0
    top_p: float = 1.0
    top_k: int = 40
    api_key: str = None

class ProcessingConfig(BaseModel):
    checkpoint_interval: int = 20
    batch_size: int = 20
    comment_column: str = "Comments"

class AppConfig(BaseModel):
    input_file: str
    output_file: str
    input_encoding: str = "utf-8"
    output_encoding: str = "utf-8-sig"
    prompt_folder: str
    llm: LLMConfig
    processing: ProcessingConfig
