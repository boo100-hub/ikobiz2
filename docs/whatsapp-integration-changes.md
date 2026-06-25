# feat: WhatsApp Cloud API — token rename, PHONE_NUMBER_ID fix, webhook setup

> Changes made to the `main` branch for WhatsApp Cloud API integration.

---

## 1. Environment Variable Rename: `WHATSAPP_TOKEN` → `IKOBIZ_META_DEV_TOKEN`

The token variable was renamed for clarity and to match Meta's developer portal naming.

### Files changed:
| File | What changed |
|------|-------------|
| `backend/app/config.py` | `WhatsAppSettings.WHATSAPP_TOKEN` → `WhatsAppSettings.META_TOKEN`. Reads `IKOBIZ_META_DEV_TOKEN` first, falls back to `WHATSAPP_TOKEN`. |
| `backend/app/whatsapp/service.py` | All `whatsapp_settings.WHATSAPP_TOKEN` → `whatsapp_settings.META_TOKEN`. Warning messages updated to reference `IKOBIZ_META_DEV_TOKEN`. |
| `backend/render.yaml` | Render env var key: `WHATSAPP_TOKEN` → `IKOBIZ_META_DEV_TOKEN` |
| `render.yaml` | Same as above |

### Rationale:
`WHATSAPP_TOKEN` is ambiguous — both WhatsApp and Instagram use similar names. `IKOBIZ_META_DEV_TOKEN` makes it clear this is a Meta developer token specific to the Ikobiz app.

---

## 2. Fix: `PHONE_NUMBER_ID` was set to WABA ID instead of Phone Number ID

### Change:
```diff
- PHONE_NUMBER_ID=1306900777746102
+ PHONE_NUMBER_ID=1051069358099923
```

The `PHONE_NUMBER_ID` in `backend/.env` was set to the **WhatsApp Business Account (WABA) ID** (`1306900777746102`). It needs to be the actual **Phone Number ID** (`1051069358099923`).

### How to verify:
```bash
# Check the WABA's phone numbers to find the correct Phone Number ID
curl -H "Authorization: Bearer $IKOBIZ_META_DEV_TOKEN" \
  "https://graph.facebook.com/v21.0/{WABA_ID}/phone_numbers"
```

### Diagnosis:
- The token (`EAAM...`) is **valid** — never-expiring system-user token for app `ikobiz` (ID `877199362069541`)
- Token has required scopes: `whatsapp_business_messaging`, `whatsapp_business_management`
- The `PHONE_NUMBER_ID` must be the ID returned by the `/phone_numbers` endpoint, **not** the WABA ID

---

## 3. Webhook Re-subscription

The WABA's webhook subscription was re-subscribed to ensure the `messages` field is enabled.

### API call:
```bash
curl -X POST "https://graph.facebook.com/v21.0/{WABA_ID}/subscribed_apps" \
  -H "Authorization: Bearer $IKOBIZ_META_DEV_TOKEN" \
  -d "subscribed_fields=messages,message_deliveries,message_reads"
```

### Webhook configuration (Meta Developer Portal):
- **Callback URL:** `https://endurance-slobbery-pantomime.ngrok-free.dev/webhook`
- **Verify token:** `ikobiz_verify_123`
- **Subscribed fields:** `messages` (ticked in Webhooks → WhatsApp section)

### Note:
The callback URL is a dynamic ngrok URL. This URL changes when ngrok is restarted (free tier). For production, a static domain or Render.com URL should replace it.

---

## Current `.env` Layout

```
# WhatsApp Cloud API (Meta)
PHONE_NUMBER_ID=1051069358099923
VERIFY_TOKEN=ikobiz_verify_123
IKOBIZ_META_DEV_TOKEN=<system_user_token>

# WhatsApp Notification Override (development only)
NOTIFY_PHONE=254714114994

# AI
GROQ_API_KEY=<groq_key>
```

---

## WhatsApp Webhook Handler Flow

```
User texts "hi"
  → Meta sends POST /webhook
  → routes.py: extract_message(body)
  → Detects "hi" → sends welcome image + text
  → get_reply("hi", sender, db):
      1. Check fulfillment flow (no)
      2. Check purchase intent (no)
      3. AI reply via Groq (if GROQ_API_KEY set)
      4. Fallback: rule-based welcome message
```

### Key files:
| File | Purpose |
|------|---------|
| `backend/app/whatsapp/routes.py` | Webhook GET (verification) + POST (inbound) endpoints |
| `backend/app/whatsapp/handler.py` | `get_reply` — fulfillment flow, purchase processing, rule-based replies |
| `backend/app/whatsapp/service.py` | `send_text_message`, `send_image_message` (async + sync) |
| `backend/app/whatsapp/ai_service.py` | Groq LLM integration |
| `backend/app/whatsapp/utils.py` | `extract_message` — parses Meta webhook payload |
| `backend/app/config.py` | `WhatsAppSettings` — reads env vars |
