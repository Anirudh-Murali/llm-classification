import asyncio
import logging
import yaml
import os

import logging
import yaml
from llm_classification.models.config import AppConfig
from llm_classification.services.orchestrator import ClassificationOrchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_env():
    """Simple .env loader to avoid extra dependencies"""
    try:
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
            logger.info("Loaded .env file")
    except Exception as e:
        logger.warning(f"Could not load .env file: {e}")

def load_config(path: str) -> AppConfig:
    load_env()
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Inject API key if present in env
    if "llm" in data and not data["llm"].get("api_key"):
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            data["llm"]["api_key"] = gemini_key
            
    return AppConfig(**data)

async def main():
    try:
        config = load_config("config.yaml")
        orchestrator = ClassificationOrchestrator(config)
        await orchestrator.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
