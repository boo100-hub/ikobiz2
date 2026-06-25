# Secondary Market Purge

Removed all IkobizListing (second-hand listing / negotiation / bidding) code from the codebase.

## What was removed

### Backend
- `models/secondary_product.py` — IkobizListing model
- `models/negotiation.py` — Negotiation model
- `routers/ikobiz.py` — CRUD for listings, `/seller/ikobiz-listings`
- `routers/negotiations.py` — CRUD for negotiation offers
- `routers/cart.py` — listing cart items, listing checkout, listing OrderItem creation, `GET /seller/ikobiz-orders`
- `routers/dashboard.py` — ikobiz order counting in summary
- `routers/messages.py` — listing branches in auto-reply generator, `_is_seller_for_order`, `_get_seller_for_order`
- `app/main.py` / `app.py` — ikobiz + negotiations router registrations
- `app/whatsapp/handler.py` — all listing search, listing purchase, listing context data, `_secondary_market_info`, `_format_product_results`, listing references in fulfillment flow
- `app/whatsapp/ai_service.py` — listings parameter from system prompt and `get_ai_reply`
- `seed.py` — all IkobizListing and Negotiation creation
- `models/cart.py` — `listing_id` columns and `listing` relationships from CartItem and OrderItem
- `models/__init__.py` — IkobizListing, Negotiation, IkobizListingStatus exports
- `alembic/env.py` — IkobizListing, Negotiation imports

### Frontend
- `web/app/market/` — listing browser (was already deleted)
- `web/app/dashboard/ikobiz/` — seller's listing management
- `web/app/dashboard/create-listing/` — create listing form
- `web/components/IkobizCard.tsx` — listing card component
- `web/app/dashboard/page.tsx` — ikobiz sidebar links, `/seller/ikobiz-orders` fetch
- `web/app/dashboard/shop-settings/page.tsx` — ikobiz sidebar links
- `web/app/cart/page.tsx` — listing price/title/image/type fallbacks, `/market` link
- `web/app/page.tsx` — search redirect to `/market`, "secondary market" text
- `web/components/Navbar.tsx` — "Secondary Market" link, search redirect to `/market`
- `web/components/Footer.tsx` — market link
- `web/lib/api.ts` — `IkobizListing` type
- `web/app/layout.tsx` — "secondary market" in SEO description
- `README.md` — "secondary market" in project description

### Migration

**Revision:** `3427ceb1f266` (parent: `beb50c30c376`)

Steps (in this order to avoid FK dependency errors):
1. Drop FK constraints `cart_items_listing_id_fkey` and `order_items_listing_id_fkey`
2. Drop `listing_id` columns from `cart_items` and `order_items`
3. Drop `ikobiz_listings` and `negotiations` tables

## Run migration

```bash
cd backend && ./venv/bin/python -m alembic upgrade head
```

## If migration fails

If you get a FK error (e.g. orphan rows remain), manually delete them first:

```sql
DELETE FROM cart_items WHERE listing_id IS NOT NULL;
DELETE FROM order_items WHERE listing_id IS NOT NULL;
```

Then retry:

```bash
cd backend && ./venv/bin/python -m alembic upgrade head
```

## If you need to regenerate the seed database

```bash
cd backend && ./venv/bin/python seed.py
```
