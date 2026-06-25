# Seed Data Format for ChatGPT Generation

## Strategy: Two‑Phase Seeding

To save demo time, only **one shop is created live**. The other is pre-seeded so both appear during buyer discovery.

- **Phase A — Pre‑seed (run before demo)**: Users + pickup points + **TechHub Electronics shop + products**. Everything except Mama Mboga.
- **Phase B — Live demo (you type during presentation)**: Seller `mama_mboga` creates shop + products through the dashboard.

**The actual pre-seed script is `backend/seed_demo.py` — it does NOT truncate existing data, only inserts missing records.**

---

## Phase A — Pre‑seed Data (Run Before Demo)

### Users (admin + 2 sellers + 1 buyer)

| Role     | Username      | Phone         | Password   |
|----------|---------------|---------------|------------|
| admin    | admin         | 254700000000  | admin123   |
| seller   | mama_mboga    | 254702193430  | seller123  |
| seller   | techhub       | 254700000011  | seller123  |
| buyer    | demo_buyer    | 254714114994  | buyer123   |

### Pickup Points

| Name                | Area         | GPS Coordinates    |
|---------------------|--------------|--------------------|
| DeKUT Main Gate     | Nyeri        | -0.4212, 36.9493   |
| Nyeri Town Stage    | Nyeri Town   | -0.4200, 36.9470   |
| Dedan Kimathi Stage | Nyeri        | -0.4195, 36.9500   |

### Pre‑seeded Shop: TechHub Electronics

| Field             | Value                        |
|-------------------|------------------------------|
| Owner             | techhub                      |
| Phone             | 254700000011                 |
| Name              | TechHub Electronics          |
| Slug              | techhub-electronics          |
| Description       | Quality electronics and phone accessories at affordable prices in Westlands. |
| Banner image      | https://images.unsplash.com/photo-1498049794561-7780e7231661       |
| Category          | electronics                  |
| Location area     | Westlands                    |
| Pickup address    | Westlands Mall, 1st Floor, Shop 7, Nairobi |
| Fulfillment modes | pickup, seller_delivery      |
| Delivery radius   | 10 km                        |
| Delivery fee      | KSh 200                      |
| Payment methods   | mpesa, cash_on_delivery      |
| Operating hours   | Mon–Fri 9:00–20:00, Sat 9:00–18:00, Sun closed |

#### Products

| Title           | Price | Stock | Description |
|-----------------|-------|-------|-------------|
| Phone Charger   | KSh 500 | 30 | Universal micro‑USB phone charger, 2A fast charging. |
| USB Cable       | KSh 300 | 40 | 1m braided USB‑A to micro‑USB cable, durable. |
| Earphones       | KSh 800 | 25 | In‑ear stereo earphones with mic, compatible with all smartphones. |
| Power Bank      | KSh 1,500 | 20 | 10,000mAh portable power bank, dual USB output. |

---

## Phase B — Live Demo Seller Data (Create During Presentation)

You create this shop + products through the seller dashboard UI while presenting.

### Shop: Mama Mboga Fresh Produce

| Field             | Value                        |
|-------------------|------------------------------|
| Owner             | mama_mboga                   |
| Phone             | 254702193430                 |
| Name              | Mama Mboga Fresh Produce     |
| Slug              | mama-mboga-fresh-produce     |
| Description       | Fresh farm produce delivered daily from local farmers in Kawangware. |
| Banner image      | https://images.unsplash.com/photo-1488459716781-31db52582fe9       |
| Category          | food                         |
| Location area     | Kawangware                   |
| Pickup address    | Kawangware Market, Stage 14, Nairobi |
| Fulfillment modes | pickup                       |
| Payment methods   | mpesa, cash                  |
| Operating hours   | Mon–Sat 6:00–18:00, Sun 7:00–13:00 |

#### Products

| Title               | Price/kg | Stock | Description |
|---------------------|----------|-------|-------------|
| Fresh Tomatoes      | KSh 120  | 50 kg | Ripe, juicy locally grown tomatoes. Perfect for stews and salads. |
| Fresh Onions        | KSh 100  | 40 kg | Red and white onions from local farms. |
| Fresh Potatoes      | KSh 80   | 60 kg | Washed, premium Kenyan potatoes (ngwaci). |
| Fresh Kale (Sukuma) | KSh 50   | 45 kg | Bunch of fresh sukuma wiki — a Kenyan staple. |

---

## Pre‑seed Script

Use the existing `backend/seed_demo.py`. It:

1. Does NOT truncate any tables — only inserts missing records
2. Creates all 4 users if they don't already exist (checked by `username`)
3. Creates 3 pickup points if they don't already exist (checked by `name`)
4. Creates the TechHub shop + its 4 products if they don't already exist
5. Leaves `mama_mboga` with no shops — ready for live demo creation
6. Handles phone conflict: if `john` (existing seller) has `254714114994`, moves him to `254714114995`

Run with:
```bash
cd backend && venv/bin/python seed_demo.py
```
