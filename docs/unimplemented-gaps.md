# Unimplemented Features & Gaps — Comprehensive Audit

Generated from deep codebase audit.

---

## CRITICAL (will crash or block users)

| # | Gap | Where | Type |
|---|---|---|---|
| 1 | `OrderStatus.PAID` used but doesn't exist in enum (PENDING/CONFIRMED/DISPATCHED/DELIVERED/CANCELLED only) | `handler.py:110,700,767` | Runtime crash |
| 2 | `OrderStatus.SHIPPED` used but doesn't exist in enum | `handler.py:946` | Runtime crash |
| 3 | Duplicate `chat_messages` migration — `6a4bcfb4deb4` and `2c96f31aa0b0` both create same table | `alembic/versions/` | `alembic upgrade head` fails |
| 4 | `/shops/page.tsx` missing — navbar and homepage search navigate here, but no route exists | `web/app/` | 404 on search |
| 5 | Groq API key returns 401 — AI conversational replies silently fail | `.env` / `ai_service.py` | AI replies don't work |
| 6 | `CheckoutRequest` is empty `pass` class — web checkout ignores request body entirely | `routers/cart.py:24` | No delivery/payment data collected via web |
| 7 | M-Pesa STK Push / payment processing — no Daraja client, no STK push, no payment callback webhook | Entire codebase | Cannot process payments |
| 8 | No M-Pesa payment callback endpoint — no webhook for Safaricom to POST confirmation to | Backend | Missing |

---

## HIGH

| # | Gap | Where |
|---|---|---|
| 9 | `category` query param accepted but never applied in `GET /products` | `routers/products.py:50-57` |
| 10 | `category` and `attributes` fields not passed to Product constructor on create/update | `routers/products.py:162-170` |
| 11 | `category` and `attributes` excluded from all product response dicts | `routers/products.py` |
| 12 | No pagination on any list endpoint (`/products`, `/orders`, `/shops`, `/seller/*`) | All list routes |
| 13 | No `loading.tsx` / `error.tsx` / `not-found.tsx` anywhere in Next.js app router | `web/app/` |
| 14 | `.catch(() => {})` silent error swallowing in 8 frontend components | Multiple `.tsx` files |
| 15 | `API_BASE` hardcoded in 5 places instead of single env var | `lib/api.ts`, 3 dashboard pages, `next.config.ts` |
| 16 | `any` types used in 24 places bypassing TypeScript safety | Multiple `.tsx` files |
| 17 | No `.env` / `.env.local` for frontend — `NEXT_PUBLIC_API_URL` never set | `web/` |
| 18 | `next.config.ts` rewrite proxy is dead code — frontend never uses `/api/` prefix | `web/next.config.ts` |
| 19 | Two diverging FastAPI entry points (`app/main.py` vs `app.py`) — `app.py` missing 3 routers | `backend/` |
| 20 | `alembic/env.py` imports outdated model list — missing `Offer`, `ChatMessage` | `alembic/env.py:36` |
| 21 | `delivery_location`/`delivery_method` in migration `2e97df3f09b7` but model uses `delivery_area`/`fulfillment_method` | Schema mismatch |
| 22 | No stock validation on web checkout | `routers/cart.py` |
| 23 | No seller registration / "become a seller" intent handler in WhatsApp flow | `handler.py` |

---

## MEDIUM

| # | Gap | Where |
|---|---|---|
| 24 | `alert()` used for all user feedback (10 places) — blocks UI, poor UX | Multiple `.tsx` |
| 25 | Quantity selector capped at 10 items on product detail page | `product/[id]/page.tsx:77` |
| 26 | Image upload logic duplicated in 3 places (inventory, shop-settings, onboarding) | Multiple pages |
| 27 | `_format_ksh`, `_is_seller_for_order`, `_notify_via_whatsapp` each defined twice | `cart.py`, `messages.py`, `handler.py` |
| 28 | Order filter input in dashboard does nothing (dead UI element) | `dashboard/page.tsx:221-228` |
| 29 | Fallback `Date.now()` used as `order_id` when API response lacks it | `cart/page.tsx:51`, `product/[id]/page.tsx:40` |
| 30 | No buyer-side cancel button on order tracking page | `checkout/[id]/page.tsx` |
| 31 | No "Out of Stock" message on product detail — buttons just disappear | `product/[id]/page.tsx:71-89` |
| 32 | WhatsApp placeholder number `254700000000` hardcoded in footer | `Footer.tsx:34` |
| 33 | `console.error` left in production code (onboarding page) | `onboarding/page.tsx:193` |
| 34 | Slugify is naive — no unicode support, no deduplication logic | `routers/shops.py:23-25` |
| 35 | No API versioning (`/v1/` prefix) | All routes |
| 36 | `SECRET_KEY` default `"change-this-secret-key-in-production"` | `core/config.py:19` |
| 37 | Migration `3c50989adc14` creates redundant `ix_chat_messages_id` index | `alembic/versions/` |
| 38 | Hardcoded DB URL in `alembic.ini` | `alembic.ini:89` |
| 39 | No buyer cancellation in WhatsApp flow (buyer markers exist but no cancel endpoint) | `handler.py` |
| 40 | `ChatMessage.sender` column `String(20)` too short for full phone numbers | `models/chat.py` |

---

## LOW — WhatsApp Specific

| # | Gap | Where |
|---|---|---|
| 41 | Voice note support — no Groq Whisper transcription for incoming audio | `handler.py` |
| 42 | Image handling — incoming images from customers not stored/forwarded | `handler.py` |
| 43 | Location sharing — WhatsApp location pins not parsed or stored | `handler.py` |
| 44 | Swahili / local language support — not in AI system prompt or rule-based replies | `ai_service.py`, `handler.py` |
| 45 | Hyperlocal search — no Haversine distance query or delivery-radius filtering | `routers/products.py` |
| 46 | Vector / semantic search — still using SQL ILIKE, no pgvector | `routers/products.py` |
| 47 | `PHONE_NUMBER_ID` not configured for production | `.env` |
| 48 | Webhook URL still uses ngrok — needs production Render URL | Meta Developer Portal |
| 49 | Legacy WhatsApp service at `services/whatsapp_service.py` returns placeholder | `services/` |
| 50 | Legacy WhatsApp router `POST /whatsapp/webhook` returns placeholder | `routers/whatsapp.py` |
| 51 | No stock validation in WhatsApp checkout path (only checks `< 1`) | `handler.py:328` |

---

## DOCUMENTATION / CLEANUP

| # | Gap | Where |
|---|---|---|
| 52 | No test files anywhere (zero pytest, zero Jest) | Entire repo |
| 53 | `.env.render` committed with live production secrets | Root |
| 54 | README stale — still references purged secondary market | `README.md` |
| 55 | `DEPLOYMENT_GUIDE.md` doesn't exist but README links it | `README.md:76` |
| 56 | No API docs (webhook format, message endpoints, order schema) | — |
| 57 | No environment setup guide (env vars, ngrok, webhook registration) | — |
| 58 | No deployment checklist (Render env vars, migrations, webhook URL) | — |

---

## PHASE 2 / VISION

| # | Gap | Source |
|---|---|---|
| 59 | Real-time dashboard chat (WebSockets/SSE) | HANDOFF.md, prj_outline.md |
| 60 | Conversation router — AI→human escalation on intent signals | HANDOFF.md, prj_outline.md |
| 61 | Model A — Shared Thread handoff (WhatsApp shared-thread API) | prj_outline.md |
| 62 | Dashboard analytics — product views, order volume trends, search terms | HANDOFF.md, implementation-plan.md |
| 63 | Platform escrow payments — M-Pesa Business till → hold → release | prj_outline.md |
| 64 | Dashboard conversation inbox with AI summaries and quick-replies | prj_outline.md |
| 65 | AI-assist features — suggested responses, auto-fill, flag urgent | prj_outline.md |
| 66 | Courier integration / third-party logistics | prj_outline.md |
| 67 | Voice commerce — voice note search in local languages | prj_outline.md |
| 68 | Pickup station network — rural and campus collection points | prj_outline.md |
| 69 | Reputation / review system — seller verification badges, ratings | prj_outline.md |
| 70 | Financial services — loans/credit from transaction history | prj_outline.md |
| 71 | Card payments & bank transfers | prj_outline.md |
| 72 | Business analytics / demand intelligence | prj_outline.md |
| 73 | Offline SMS fallback for feature phones | prj_outline.md |
| 74 | B2B commerce / supplier restocking | prj_outline.md |
| 75 | Multi-language / i18n framework | prj_outline.md |
| 76 | Password reset / email verification flow | — |
| 77 | Admin panel endpoints | — |
| 78 | Refund / dispute handling | — |
| 79 | Shipping tracking / carrier integration | — |
