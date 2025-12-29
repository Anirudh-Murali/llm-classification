# Multi-Task Configuration Guide

This service supports multiple classification tasks by switching between different prompt folders.

## Structure

Each classification task should have its own folder under `prompts/`:

```
prompts/
├── mh_farmers_greivence/          # Maharashtra farmers grievance classification
│   ├── system_prompt.txt          # Main prompt template
│   └── categories/                # Category definitions
│       ├── category1.txt
│       ├── category2.txt
│       └── ...
│
└── another_task/                  # Another classification task
    ├── system_prompt.txt
    └── categories/
        ├── categoryA.txt
        └── categoryB.txt
```

## System Prompt Template

The `system_prompt.txt` file should contain your classification instructions with a `{{CATEGORIES}}` placeholder where the category definitions will be injected:

```
You are an expert classification system.

Your task is to classify the input into ONE of the categories defined below.

**CATEGORIES:**
{{CATEGORIES}}

**OUTPUT FORMAT:**
Return JSON: {"category": "category_name", "reasoning": "explanation"}
```

## Category Files

Each category is defined in a separate `.txt` file in the `categories/` subfolder:

**Example** (`categories/technical_issues.txt`):
```
Definition: Technical problems with systems, portals, or applications.

Keywords:
login error, system crash, page not loading, upload failed, ...
```

## Configuration

Switch between tasks in `config.yaml`:

```yaml
prompt_folder: "prompts/mh_farmers_greivence"  # Current task

# OR switch to another task:
# prompt_folder: "prompts/another_task"
```

## How It Works

1. **PromptManager** loads the specified `prompt_folder`
2. Reads `system_prompt.txt` as a template
3. Discovers all `.txt` files in `categories/` subfolder
4. Builds category section from discovered files
5. Injects categories into the `{{CATEGORIES}}` placeholder
6. Final prompt is sent to the LLM

## Adding a New Classification Task

1. Create a new folder: `prompts/<task_name>/`
2. Add `system_prompt.txt` with classification instructions and `{{CATEGORIES}}` placeholder
3. Create `categories/` subfolder
4. Add category definition files (`.txt`)
5. Update `config.yaml`: `prompt_folder: "prompts/<task_name>"`
6. Run the service

## Benefits

✅ **No code changes** - just add new folders
✅ **Automatic category discovery** - add/remove categories dynamically
✅ **Reusable architecture** - same code for different classification tasks
✅ **Type-safe** - categories validated at runtime
✅ **Easy to maintain** - each task is self-contained
