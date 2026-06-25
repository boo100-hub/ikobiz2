# feat: Shop fulfillment fields — backend persistence + frontend settings + delivery fee

## Changes Made

### 1. Backend — POST/PUT /shops now persist all fulfillment fields

`backend/routers/shops.py`

`create_shop()` and `update_shop()` were only saving `name`, `description`, `banner_image`. All `ShopCreate`/`ShopUpdate` fields are now written to the database:

- `category`, `location_area`, `location_gps_lat`, `location_gps_lng`
- `fulfillment_modes`, `delivery_radius_km`, `delivery_fee`
- `operating_hours`, `payment_methods`, `pickup_address`, `phone`

### 2. Frontend — Shop Settings page

`web/app/dashboard/shop-settings/page.tsx` (new)

Full settings form for sellers:
- Shop name, description, banner image
- Category dropdown (food, electronics, fashion, health, home, sports, services, agriculture, other)
- Location area
- Fulfillment modes (checkboxes: pickup, seller delivery)
- Delivery radius (km) and fee (KES)
- Operating hours (JSON string format)
- Payment methods (checkboxes: M-Pesa, Cash on Delivery, Bank Transfer)
- Pickup address
- Contact phone
- Multi-shop selector if seller has multiple shops

Sidebar nav link added to all dashboard pages (`dashboard/page.tsx`, `dashboard/ikobiz/page.tsx`, `dashboard/create-listing/page.tsx`).

### 3. WhatsApp handler — delivery fee uses shop config

`backend/app/whatsapp/handler.py`

`_build_order_summary()` and `_finalize_fulfillment()` now read `shop.delivery_fee` from the product's shop instead of hardcoding 200. Falls back to 200 if no fee is set.

## Files changed

| File | Change |
|------|--------|
| `backend/routers/shops.py` | POST/PUT now persist all fulfillment fields |
| `web/app/dashboard/shop-settings/page.tsx` | New shop settings form page |
| `web/app/dashboard/page.tsx` | Added sidebar link to shop settings |
| `web/app/dashboard/ikobiz/page.tsx` | Added sidebar link to shop settings |
| `web/app/dashboard/create-listing/page.tsx` | Added sidebar link to shop settings |
| `backend/app/whatsapp/handler.py` | Use shop.delivery_fee instead of hardcoded 200 |
