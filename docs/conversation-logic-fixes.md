# fix: conversation logic — purchase intent, product search, fulfillment guards

## Changes Made

### 1. Purchase keywords narrowed
`PURCHASE_KEYWORDS` was reduced from 10 entries to 4:

```diff
- {"buy", "purchase", "order", "i want", "i need", "i will buy", "i will get", "i would like", "get me", "procure"}
+ {"buy", "purchase", "order", "procure"}
```

**Why:** "i want shoes" was triggering an immediate buy flow without showing search results first. Now only explicit purchase commands auto-start fulfillment. Softer intents flow to AI or rule-based search.

### 2. General product search added to rule-based fallback
`backend/app/whatsapp/handler.py` — the rule-based fallback in `get_reply()` previously only searched:
- Shops by name
- Second-hand listings (`IkobizListing`)

Now it also searches **regular shop products** (`Product`) when neither of the above match. Results are grouped by shop for readability with a new `_format_product_search_results()` function.

### 3. Question detection in fulfillment flow
`backend/app/whatsapp/handler.py` — the "location" step in `_handle_fulfillment_step()` now rejects input that looks like a question:

```python
if "?" in text or lower.startswith(("which", "what", "who", "how", ...)):
    return "📍 I still need your delivery area..."
```

**Why:** "which shoe am i getting?" was being accepted as a delivery address, advancing the flow to payment.

### 4. STOP_WORDS expanded
Added `"want"`, `"need"`, `"looking"` so `_extract_product_query()` produces cleaner search terms (e.g., "i want shoes" → "shoes" not "want shoes").

## Files changed
| File | Change |
|------|--------|
| `backend/app/whatsapp/handler.py` | Purchase keywords, product search formatter, fulfillment guards, stop words |

## Related
- A valid `GROQ_API_KEY` is still needed — the current one returns 401
