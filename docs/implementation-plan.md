# Implementation Plan — WhatsApp-Native AI Commerce Network

> **Rule:** Every time a feature is implemented, updated, or fixed, update the relevant `docs/` file immediately. If no doc exists for the feature, create one. This keeps the repo merge-friendly and lets collaborators compare what's been done vs what they're working on.

---

## Action Items

### Setup & Configuration

- [ ] **1.** Fix `PHONE_NUMBER_ID` in `.env` — ensure it's the Phone Number ID, not the WABA ID (`docs/whatsapp-integration-changes.md`)
- [ ] **2.** Configure webhook callback URL in Meta Developer Portal (WhatsApp → Configuration) and subscribe to `messages` field (`docs/whatsapp-integration-changes.md`)

### Conversations & Messaging

- [x] **3.** Seller handoff (Model C — redirect to seller's WhatsApp). After order confirmation, send customer a `wa.me` link with seller's phone + prefilled order message. Platform retains structured order data. Seller takes over on their personal WhatsApp.
- [x] **4.** Fix AI + conversation bugs. Purged soft purchase keywords ("i want", "i need", etc.) from auto-buy trigger — only "buy"/"purchase"/"order" start purchase. Added general product search to rule-based fallback. Added question detection ("which"/"what"/"?" etc.) to fulfillment flow so questions aren't consumed as location/payment inputs. Added "want"/"need"/"looking" to STOP_WORDS for cleaner search extraction.
- [ ] **5.** Voice note support — transcribe incoming voice messages via Groq Whisper API, feed into existing text pipeline
- [ ] **6.** Image handling — accept incoming images from customers (store, log, forward to seller)
- [ ] **7.** Location sharing — handle WhatsApp location messages (pins) and store coordinates
- [ ] **8.** Swahili / local language support — add to AI system prompt and rule-based replies

### Order & Fulfillment

- [x] **8.** Seller notification on new order — WhatsApp message to seller with order summary (via `_notify_via_whatsapp` in both `handler.py` and `cart.py`)
- [x] **9.** Order status updates — automated "confirmed → dispatched → delivered" messages sent to customer via WhatsApp on each PATCH /orders/{id}/status
- [ ] **10.** Order cancellation — allow customer to cancel within a window; notify seller

### Discovery & Search

- [ ] **11.** Hyperlocal search — filter products by seller location radius; support typed area names
- [ ] **12.** Vector / semantic search — replace SQL `ILIKE` with pgvector embeddings (post-MVP)

### Seller Dashboard

- [x] **13.** Order management in dashboard — confirm, dispatch, mark delivered, view order history with fulfillment/payment/customer details
- [x] **13b.** Shop settings page at `/dashboard/shop-settings` — full form for category, location, fulfillment modes, delivery radius/fee, operating hours, payment methods, pickup address, phone, banner image
- [x] **13c.** POST/PUT /shops endpoints now persist all 10 fulfillment fields (were silently dropped)
- [x] **13d.** Purged all secondary market code — IkobizListing, Negotiation, bidding, `/market` routes, listing cart/checkout, listing auto-replies, listing WhatsApp purchase flow, listing context data, `/seller/ikobiz-orders` endpoint; added Alembic migration to drop `listing_id` columns and `ikobiz_listings` / `negotiations` tables (`docs/secondary-market-purge.md`)
- [ ] **14.** Inventory management in dashboard — add/edit products, update stock, upload photos
- [ ] **15.** Dashboard analytics — product views, order volume, customer search terms

### Phase 2 — Model A (Shared Thread)

- [ ] **16.** Dashboard → WhatsApp live chat — seller sees live conversation, can type or click AI-suggested replies
- [ ] **17.** Conversation router — AI handles discovery & standard questions; escalates to seller on intent signals (custom request, negotiation, high value)
- [ ] **18.** Real-time infrastructure — WebSockets or SSE for live chat in dashboard

### Payments

- [ ] **19.** M-Pesa integration — generate STK push or provide seller till; confirm payment via API

### Documentation

- [ ] **20.** API docs — document webhook format, message endpoints, order object schema
- [ ] **21.** Environment setup guide — document all env vars, ngrok setup, webhook registration steps
- [ ] **22.** Deployment checklist — steps for Render.com deploy (env vars, webhook URL update, database migration)
