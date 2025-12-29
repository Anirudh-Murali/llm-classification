import asyncio
import logging
import yaml
from llm_classification.models.config import AppConfig
from llm_classification.services.orchestrator import ClassificationOrchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(path: str) -> AppConfig:
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
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
