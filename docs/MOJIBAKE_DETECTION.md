# Mojibake Detection Feature

## Overview

The service now automatically detects and skips corrupted text (mojibake) before sending to the LLM, saving API calls and improving efficiency.

## How It Works

**Mojibake** is text corruption that occurs when UTF-8 encoded text (like Devanagari/Marathi) is incorrectly decoded as Latin-1. This results in garbage characters like:
- `à¤¸à¤°` instead of `सर`
- `à¤¶à¤¿à¤µà¤¾à¤œà¥€` instead of `शिवाजी`

### Detection Algorithm

The `is_mojibake()` function in `text_utils.py`:
1. Searches for common mojibake patterns (`à¤`, `à¥`, etc.)
2. Calculates the ratio of mojibake characters to total text
3. If ratio exceeds 15% threshold, marks as mojibake

### Processing Flow

```
┌─────────────┐
│  Read Row   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Check Text      │
│ Quality         │
└──────┬──────────┘
       │
       ├──► Empty? ────────┐
       │                   │
       ├──► Mojibake? ─────┤
       │                   │
       ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ Call LLM     │    │ Skip LLM     │
│ Classify     │    │ Set NULL     │
└──────────────┘    └──────────────┘
```

## Output Format

For skipped rows, the CSV output contains:
- `grievance_category`: `null` (empty cell)
- `reasoning`: `"skipped_mojibake"` or `"skipped_empty"`

Example output:
```csv
TicketNumber,Comments,grievance_category,reasoning
20240808001435,"à¤¸à¤° à¤†à¤®...",,"skipped_mojibake"
20220522211607,"Please solve problem",system_portal_issues,"Login and submission related..."
```

## Configuration

Mojibake threshold can be adjusted in `text_utils.py`:

```python
is_mojibake(text, threshold=0.15)  # Default: 15% mojibake chars
```

Lower threshold = more aggressive detection
Higher threshold = more lenient

## Statistics

After running, check the summary:
- Rows with `skipped_mojibake` were detected as corrupted
- Rows with `skipped_empty` had no content
- Other rows were successfully classified by LLM

## Benefits

✅ **Cost Savings**: No wasted LLM API calls on unreadable text
✅ **Performance**: Faster processing (skip LLM latency)
✅ **Data Quality**: Clear marking of problematic data
✅ **Transparency**: Easy to identify and fix source data issues
