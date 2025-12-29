# Multi-Task Architecture - Implementation Summary

## What Changed

Refactored the service to support **multiple classification tasks** by making the prompt system configurable and template-based.

## Key Changes

### 1. Configuration (`config.yaml`)
Added `prompt_folder` parameter:
```yaml
prompt_folder: "prompts/mh_farmers_greivence"
```

### 2. Prompt Structure
```
prompts/
└── mh_farmers_greivence/           # Task-specific folder
    ├── system_prompt.txt           # Template with {{CATEGORIES}} placeholder
    └── categories/                 # Category definitions
        ├── system_portal_issues.txt
        ├── departmental_process_delays.txt
        └── ...
```

### 3. Template System
**System Prompt Template** (`system_prompt.txt`):
- Contains classification instructions
- Has `{{CATEGORIES}}` placeholder
- PromptManager injects discovered categories at runtime

### 4. Removed Static Enum
- Changed `category` field from `GrievanceCategory` enum to `str`
- Categories now discovered dynamically from filesystem
- More flexible for different classification tasks

### 5. Updated PromptManager
**New methods**:
- `__init__(prompt_folder)` - Takes folder path instead of categories dir
- `_build_categories_section()` - Formats categories for injection
- `get_valid_categories()` - Returns list of valid category names

**Flow**:
1. Load `system_prompt.txt` as template
2. Discover all `.txt` files in `categories/` subfolder
3. Build formatted category section
4. Replace `{{CATEGORIES}}` placeholder
5. Return final prompt

### 6. Updated Models
- `AppConfig` now has `prompt_folder: str` field
- `GrievanceRow.category` changed from enum to `str`

## Benefits

✅ **Multi-task support**: Switch classification tasks by changing one config line
✅ **No code changes**: Add new tasks by creating new folders
✅ **Dynamic categories**: Categories auto-discovered from files
✅ **Template-based**: Easy to customize prompts without touching code
✅ **Maintainable**: Each task is self-contained

## How to Use

### Switch to Different Task
```yaml
# config.yaml
prompt_folder: "prompts/another_classification_task"
```

### Add New Classification Task
1. Create `prompts/new_task/`
2. Add `system_prompt.txt` with `{{CATEGORIES}}` placeholder
3. Add `categories/*.txt` files
4. Update config
5. Run!

## Example: Adding a Customer Support Task

```bash
mkdir -p prompts/customer_support/categories
```

**Create** `prompts/customer_support/system_prompt.txt`:
```
Classify customer support tickets into categories.

**CATEGORIES:**
{{CATEGORIES}}

Return JSON: {"category": "name", "reasoning": "why"}
```

**Add categories**: 
- `prompts/customer_support/categories/billing.txt`
- `prompts/customer_support/categories/technical.txt`
- etc.

**Update config**:
```yaml
prompt_folder: "prompts/customer_support"
```

## Testing

Service was tested with existing data and successfully:
- ✅ Loaded custom system prompt template
- ✅ Discovered categories from new folder structure
- ✅ Injected categories into template
- ✅ Processed 120 rows with new structure
- ✅ Resumed from checkpoint correctly

## Files Modified

1. `config.yaml` - Added `prompt_folder`
2. `llm_classification/models/config.py` - Added `prompt_folder` field
3. `llm_classification/models/data.py` - Changed category to `str`
4. `llm_classification/services/prompt_manager.py` - Complete refactor
5. `llm_classification/services/orchestrator.py` - Use `config.prompt_folder`

## Files Created

1. `prompts/mh_farmers_greivence/system_prompt.txt` - Template prompt
2. `prompts/README.md` - Multi-task configuration guide

## Migration from Old Structure

Old:
```
prompts/categories/
    ├── category1.txt
    └── category2.txt
```

New:
```
prompts/task_name/
    ├── system_prompt.txt
    └── categories/
        ├── category1.txt
        └── category2.txt
```

Your existing categories were moved to `prompts/mh_farmers_greivence/categories/`.
