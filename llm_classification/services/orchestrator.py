import os
import pandas as pd
import asyncio
import logging
from typing import List, Dict, Any
from tqdm.asyncio import tqdm

from ..models.config import AppConfig
from ..llm_clients.base import BaseLLMClient
from ..llm_clients.ollama import OllamaClient
from .prompt_manager import PromptManager
from .text_utils import get_text_quality_issue
from ..models.response import ClassificationResponse

logger = logging.getLogger(__name__)

class ClassificationOrchestrator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.prompt_manager = PromptManager(config.prompt_folder)
        self.llm_client = self._get_llm_client()
        self.system_prompt = self.prompt_manager.get_system_prompt()
        self.semaphore = asyncio.Semaphore(config.llm.max_concurrency)
        self.valid_categories = self.prompt_manager.get_valid_categories()

    def _get_llm_client(self) -> BaseLLMClient:
        if self.config.llm.provider == "ollama":
            return OllamaClient(self.config.llm)
        else:
            raise ValueError(f"Unsupported provider: {self.config.llm.provider}")

    def _get_processed_count(self) -> int:
        if not os.path.exists(self.config.output_file):
            return 0
        try:
            # Check if file has header
            with open(self.config.output_file, 'r', encoding=self.config.output_encoding) as f:
                first_line = f.readline()
                if not first_line:
                    return 0
            # Count lines - 1 for header
            count = sum(1 for _ in open(self.config.output_file, encoding=self.config.output_encoding)) - 1
            return max(0, count)
        except Exception as e:
            logger.error(f"Error checking output file: {e}")
            return 0

    async def _classify_single(self, row: pd.Series) -> Dict[str, Any]:
        text = str(row[self.config.processing.comment_column])
        
        # Check for text quality issues
        quality_issue = get_text_quality_issue(text)
        
        if quality_issue:
            # ... skip logic ...
            return {
                **row.to_dict(),
                "grievance_category": None,
                "reasoning": f"skipped_{quality_issue}",
                "language": None,
                "translation": None
            }

        async with self.semaphore:
            # Get JSON schema from Pydantic model
            schema = ClassificationResponse.model_json_schema()
            result = await self.llm_client.aclassify(text, self.system_prompt, schema=schema)
            # print(f"DEBUG LLM RESULT: {result}")
        
        return {
            **row.to_dict(),
            "grievance_category": result.get("category"),
            "reasoning": result.get("reasoning"),
            "language": result.get("language"),
            "translation": result.get("translation")
        }

    async def run(self):
        logger.info(f"Starting classification. Input: {self.config.input_file}")
        
        # Determine where to resume
        processed_count = self._get_processed_count()
        logger.info(f"Resuming from row {processed_count}")

        # Read CSV in chunks
        chunk_size = self.config.processing.checkpoint_interval
        
        # Skip rows logic: define rows to skip (1-based index usually for skiprows, but we want to skip top N rows)
        # pandas skiprows: line numbers to skip (0-indexed) or number of lines.
        # simpler: read_csv(..., skiprows=range(1, processed_count + 1)) so header (0) is kept
        
        skip_range = range(1, processed_count + 1) if processed_count > 0 else None
        
        try:
            # We iterate specifically to handle large files
            # Note: pandas chunksize returns an iterator
            reader = pd.read_csv(
                self.config.input_file,
                skiprows=skip_range,
                chunksize=chunk_size,
                encoding=self.config.input_encoding,
                encoding_errors='replace'  # Replace invalid chars with �
            )
        except ValueError:
            # Might happen if file is empty or processed_count exceeds lines
            logger.info("No more rows to process.")
            return

        total_processed = processed_count
        
        for chunk_df in reader:
            tasks = []
            for _, row in chunk_df.iterrows():
                tasks.append(self._classify_single(row))
            
            results = await asyncio.gather(*tasks)
            
            # Convert to DataFrame
            results_df = pd.DataFrame(results)
            
            # Append to output
            header = not os.path.exists(self.config.output_file)
            results_df.to_csv(
                self.config.output_file, 
                mode='a', 
                header=header, 
                index=False,
                encoding=self.config.output_encoding
            )
            
            total_processed += len(results)
            print(f"Processed {total_processed} rows...")

        logger.info("Classification completed.")
