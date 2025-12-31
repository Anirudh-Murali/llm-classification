import os
import pandas as pd
import asyncio
import logging
from typing import List, Dict, Any
from tqdm.asyncio import tqdm

from ..models.config import AppConfig
from ..llm_clients.base import BaseLLMClient
from ..llm_clients.ollama import OllamaClient
from ..llm_clients.gemini import GeminiClient

from .prompt_manager import PromptManager
from .text_utils import get_text_quality_issue
from ..models.response import ClassificationResponse, BatchClassificationResponse

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
        elif self.config.llm.provider == "gemini":
            return GeminiClient(self.config.llm)
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

    async def _classify_batch(self, rows: List[pd.Series]) -> List[Dict[str, Any]]:
        batch_inputs = []
        # Map TicketNumber -> Original Row Index
        id_map = {}
        results_map = {}
        
        # 1. First pass: Filter mojibake/empty and prepare inputs
        for idx, row in enumerate(rows):
            text = str(row[self.config.processing.comment_column])
            ticket_id = str(row["TicketNumber"]) # Assume TicketNumber exists per user request
            
            quality_issue = get_text_quality_issue(text)
            
            if quality_issue:
                # Mark skipped immediately
                results_map[idx] = {
                    **row.to_dict(),
                    "grievance_category": None,
                    "reasoning": f"skipped_{quality_issue}",
                    "language": None,
                    "translation": None
                }
            else:
                batch_inputs.append((ticket_id, text))
                id_map[ticket_id] = idx
        
        # 2. Call LLM for valid inputs
        if batch_inputs:
            formatted_input = "\n".join([f"ID: {tid}\nComment: {text}\n" for tid, text in batch_inputs])
            
            try:
                # Get schema for BATCH response
                schema = BatchClassificationResponse.model_json_schema()
                
                async with self.semaphore:
                    llm_response = await self.llm_client.aclassify(formatted_input, self.system_prompt, schema=schema)
                
                # Parse results
                batch_results = llm_response.get("results", [])
                
                # Verify and Map back
                processed_ids = set()
                
                for result in batch_results:
                    tid = str(result.get("id"))
                    if tid in id_map:
                        idx = id_map[tid]
                        results_map[idx] = {
                            **rows[idx].to_dict(),
                            "grievance_category": result.get("category"),
                            "reasoning": result.get("reasoning"),
                            "language": result.get("language"),
                            "translation": result.get("translation")
                        }
                        processed_ids.add(tid)
                    else:
                        logger.warning(f"Received unknown ID from LLM: {tid}")
                
                # Check for missing IDs (mismatch)
                for tid, _ in batch_inputs:
                    if tid not in processed_ids:
                        idx = id_map[tid]
                        logger.warning(f"Missing result for ID: {tid}")
                        results_map[idx] = {
                             **rows[idx].to_dict(),
                            "grievance_category": "error",
                            "reasoning": "Batch mismatch: ID missing in response",
                             "language": None,
                            "translation": None
                        }
                    
            except Exception as e:
                logger.error(f"Batch failure: {e}")
                # Mark all valid inputs as error for safety
                for tid, idx in id_map.items():
                     if idx not in results_map:
                        results_map[idx] = {
                            **rows[idx].to_dict(),
                            "grievance_category": "error",
                            "reasoning": f"Batch processing failed: {str(e)}",
                             "language": None,
                            "translation": None
                        }

        # 3. Construct final list in order
        final_results = []
        for i in range(len(rows)):
            final_results.append(results_map[i])
            
        return final_results

    async def run(self):
        logger.info(f"Starting classification. Input: {self.config.input_file}")
        
        processed_count = self._get_processed_count()
        logger.info(f"Resuming from row {processed_count}")

        # Configs
        batch_size = self.config.processing.batch_size
        
        # Determine skip range
        skip_range = range(1, processed_count + 1) if processed_count > 0 else None
        
         # Get total lines for progress bar
        total_rows = 0
        try:
            with open(self.config.input_file, 'r', encoding=self.config.input_encoding, errors='replace') as f:
                total_rows = sum(1 for _ in f) - 1 # Subtract header
        except Exception:
            pass

        with tqdm(total=total_rows, initial=processed_count, unit="row", desc="Classifying") as pbar:
            try:
                reader = pd.read_csv(
                    self.config.input_file,
                    skiprows=skip_range,
                    chunksize=batch_size, # Read in batch size chunks directly
                    encoding=self.config.input_encoding,
                    encoding_errors='replace'
                )
            except ValueError:
                logger.info("No more rows to process.")
                return

            total_processed = processed_count
            
            # Create async tasks for batches
            # We will process chunks in parallel based on max_concurrency
            # Since we read in chunksize=batch_size, each chunk IS a batch
            
            # For simplicity with asyncio.gather, we can process N batches at a time
            # But reader is an iterator.
            # Efficient pattern: Use a bounded semaphore with asyncio tasks
            
            pending_tasks = []
            
            for chunk_df in reader:
                rows = [row for _, row in chunk_df.iterrows()]
                
                # Create task
                task = asyncio.create_task(self._classify_batch(rows))
                pending_tasks.append(task)
                
                # If we have enough tasks, wait for them
                # We limit pending tasks to, say, max_concurrency * 2 to keep pipeline full
                # But our semaphore already limits LLM calls.
                # So we can just gather them periodically to write to disk.
                
                # To respect checkpoint_interval, let's accumulate results
                if len(pending_tasks) >= self.config.llm.max_concurrency:
                    completed_batches = await asyncio.gather(*pending_tasks)
                    pending_tasks = []
                    
                    # Flatten results
                    all_results = [item for batch in completed_batches for item in batch]
                    
                    # Write
                    results_df = pd.DataFrame(all_results)
                    header = not os.path.exists(self.config.output_file)
                    results_df.to_csv(
                        self.config.output_file, 
                        mode='a', 
                        header=header, 
                        index=False,
                        encoding=self.config.output_encoding
                    )
                    
                    count = len(all_results)
                    total_processed += count
                    pbar.update(count)
            
            # Process remaining tasks
            if pending_tasks:
                completed_batches = await asyncio.gather(*pending_tasks)
                all_results = [item for batch in completed_batches for item in batch]
                results_df = pd.DataFrame(all_results)
                header = not os.path.exists(self.config.output_file)
                results_df.to_csv(
                    self.config.output_file, 
                    mode='a', 
                    header=header, 
                    index=False,
                    encoding=self.config.output_encoding
                )
                pbar.update(len(all_results))
                
        logger.info("Classification completed.")
