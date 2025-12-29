# Grievance Classification Service

A modular, async Python service for classifying farmer grievance comments using LLMs (Large Language Models).

## Features

- 🚀 **Async Processing**: Uses `asyncio` for concurrent LLM requests
- 💾 **Resilience**: Checkpointing system saves progress every N rows
- 🔧 **Modular Architecture**: Easy to extend with new LLM providers
- 📝 **Configuration-Driven**: YAML-based configuration
- 🏷️ **Category Management**: Simple text file-based category definitions

## Architecture

```
llm_classification/
├── llm_clients/          # LLM provider implementations
│   ├── base.py          # Abstract base class
│   ├── ollama.py        # Ollama implementation
│   └── README.md        # Guide for adding new providers
├── models/              # Data models and enums
│   ├── enums.py        # GrievanceCategory enum
│   ├── config.py       # Configuration models
│   └── data.py         # Data models
└── services/           # Core services
    ├── prompt_manager.py    # Loads categories and builds prompts
    └── orchestrator.py      # Main orchestration logic
```

## Setup

### 1. Install Dependencies

```bash
poetry install
```

### 2. Configure Ollama

Make sure Ollama is running with your model:

```bash
# Pull the model
ollama pull gemma3:14b

# Start Ollama (if not already running)
ollama serve
```

### 3. Configure the Service

Edit `config.yaml`:

```yaml
input_file: "data/sample.csv"
output_file: "data/output_classified.csv"

llm:
  provider: "ollama"
  model: "gemma3:14b"
  base_url: "http://localhost:11434"
  max_concurrency: 5  # Adjust based on your hardware
  timeout: 60

processing:
  checkpoint_interval: 10  # Save after every 10 rows
  comment_column: "Comments"  # Column name in your CSV
```

### 4. Customize Categories

Categories are defined in `prompts/categories/*.txt`. Each file contains:
- A definition line
- Keywords for matching

To add/modify categories:
1. Edit existing `.txt` files or create new ones
2. Filename (without `.txt`) becomes the category name
3. Restart the service

## Usage

### Basic Run

```bash
poetry run python llm_classification/run.py
```

### Resume After Interruption

The service automatically resumes from where it left off by checking the output file.

## How It Works

### 1. Prompt Construction

`PromptManager` loads all category files and builds a system prompt:

```
You are an expert grievance classification system.
Classify the following user input into ONE of the following categories...

CATEGORY: system_portal_issues
Definition: Issues related to the technical functioning...
Keywords: Portal not working, Login issue, ...

... (other categories)

OUTPUT FORMAT:
{"category": "category_name", "reasoning": "brief explanation"}
```

### 2. Concurrent Processing

`ClassificationOrchestrator`:
1. Reads CSV in chunks (default: 10 rows)
2. Creates async tasks for each comment
3. Uses `asyncio.Semaphore` to limit concurrency
4. Waits for all tasks in chunk to complete
5. Appends results to output CSV
6. Repeats until done

### 3. Resilience

- Progress is saved after each chunk
- On restart, the service counts rows in output file
- Skips already-processed rows using `pandas.read_csv(skiprows=...)`

## Extending the Service

### Adding a New LLM Provider

See `llm_classification/llm_clients/README.md` for detailed instructions.

Quick example for OpenAI:

```python
# llm_clients/openai_client.py
from openai import AsyncOpenAI
from .base import BaseLLMClient

class OpenAIClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self.client = AsyncOpenAI(api_key=config.api_key)
        self.model = config.model
    
    async def aclassify(self, text: str, system_prompt: str):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Comment: {text}"}
            ],
            response_format={"type": "json_object"}
        )
        # Parse and return
```

Then update `orchestrator.py` to instantiate it when `provider: "openai"`.

## Performance Tuning

- **`max_concurrency`**: Higher values = faster, but uses more memory/CPU
- **`checkpoint_interval`**: Lower = more frequent saves, but slower I/O
- **Model choice**: Smaller models are faster but may be less accurate

## Troubleshooting

### "Connection refused" error
- Ensure Ollama is running: `ollama serve`
- Check `base_url` in config matches Ollama's address

### Slow processing
- Increase `max_concurrency` if your system can handle it
- Use a smaller/faster model
- Check if Ollama is using GPU acceleration

### Out of memory
- Decrease `max_concurrency`
- Decrease `checkpoint_interval` to flush results more frequently

## License

MIT
