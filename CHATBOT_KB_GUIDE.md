# AI Assistant Knowledge Base Guide

This guide explains the lightweight in-app knowledge base (KB) used by the AI Assistant to answer questions about proposals, navigation, pricing, and how to find resources.

## What was added
- `chatbot_kb.py`: A small, dependency-free matcher that returns HTML-ready answers for common topics.
- `/api/ai-assistant-reply`: Backend endpoint that uses the KB to answer messages.
- `templates/ai_assistant.html`: Updated to call the backend API with graceful fallback to local suggestions if the API fails.

## Current coverage
- Proposal structure essentials
- Past performance guidance
- Pricing components and strategy
- Compliance matrix basics
- Platform navigation overview (where to find things)
- Pricing calculator walkthrough
- Subscription pricing & WIN50 discount

## How it works
1. Frontend sends `{message}` to `/api/ai-assistant-reply`.
2. Server calls `get_kb_answer(message)`.
3. The matcher checks for intent tags and keyword scores and returns `{answer, followups, source}`.
4. Frontend renders the HTML-formatted answer and optional follow-ups.

## Extending the KB
Edit `chatbot_kb.py` and add a new `KBArticle`:

```python
KBArticle(
    id="state_procurement_portals",
    title="State Procurement Portals",
    intent_tags=["navigation","state portals","portals"],
    keywords=["state","procurement","portals","bid"],
    answer=(
        "Find all state procurement portals at <a href='/state-procurement-portals'>State Portals</a>.\n"
        "Filter by state and bookmark frequent destinations."
    ),
    followups=["Ask about Virginia EVA","How to set bid alerts?", "Where to find SAM.gov?"]
)
```

Then rebuild indexes at the bottom of the file (existing code does this automatically on import).

## Testing locally
Use the project venv’s python:

```bash
".venv/bin/python" - <<'PY'
from chatbot_kb import get_kb_answer
for q in [
  "How do I structure my technical approach?",
  "Where do I find pricing calculator?",
  "WIN50 discount details",
  "past performance metrics",
  "compliance matrix format",
  "navigation help platform",
]:
    print(q, '=>', get_kb_answer(q)['source'])
PY
```

## Notes
- The KB returns HTML; links are safe internal routes or descriptive text. Avoid untrusted HTML.
- If you later add OpenAI/Claude, you can feed the KB `answer` as context for RAG-style responses.
- Keep answers concise and actionable; use links to deeper docs/pages when possible.
