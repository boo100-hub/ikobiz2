# Design Integration — Agent Instructions

## Overview

Merge the UI design from the **design project** into the **functional codebase**, preserving all existing backend-backed functionality while adopting the new design's look, feel, and component structure. Where the design introduces new features not yet backed by the backend, implement them to the extent possible (mock data patterns, UI hooks ready for future backend work). **Never remove existing functionality** — the result must be strictly additive.

---

## Project Locations

| Project | Path | Branch | Notes |
|---------|------|--------|-------|
| **Functional codebase (target)** | `/home/manu/Desktop/forked/ikobiz2/` | `main` (working tree) | Has real API calls, auth, database. Web frontend at `web/` |
| **Design project (source)** | `/home/manu/Desktop/forked/ikobiz-marketplace-design/` | N/A (separate directory) | Static UI mockup with shadcn/ui, Tailwind v4, zero API calls |

---

## Route Mapping

The design renamed several routes. When merging, **use the design's route names** and set up redirects for the old ones.

| Function | Old Route (functional) | New Route (design) | Notes |
|----------|----------------------|-------------------|-------|
| Homepage | `/` | `/` | Same |
| Search results | `/shops?q=<query>` | `/search` | Design has `/search` (not `/shops?q=`). Add `?q=` param support to `/search` page |
| Shop detail | `/shops/[slug]` | `/shop/[id]` | Design uses numeric `id`; functional uses `slug`. The design only links via `id`. Best approach: accept both `id` and `slug` params, or add a redirect |
| Product detail | `/product/[id]` | `/product/[id]` | Same |
| Cart | `/cart` | `/cart` | Same (but design adds promo code UI) |
| Checkout | embedded in `/cart` (inline form) | `/checkout` (multi-step page) | **Design adds a separate multi-step checkout flow** — new feature |
| Order tracking | `/checkout/[id]` | `/orders/[id]` | Route renamed |
| Login | `/auth/login` | `/login` | Route simplified |
| Register | `/auth/register` | `/register` | Route simplified |
| Seller Dashboard | `/dashboard` | `/seller/dashboard` | Route moved under `/seller/` |
| Seller Inventory | `/dashboard/inventory` | `/seller/inventory` | Route moved |
| Seller Orders | *(no dedicated page)* | `/seller/orders` | **New page** — sellers previously managed orders from dashboard. The design adds a dedicated orders page |
| Seller Order Detail | *(no route)* | `/seller/orders/[id]` | **New page** — design links here from orders table |
| Seller Onboarding | `/dashboard/onboarding` | `/seller/onboarding` | Route moved |
| Seller Settings | `/dashboard/shop-settings` | `/seller/settings` | Route moved |
| Add Product | *(no route, inline form)* | `/seller/inventory/new` | **New page** — design has a dedicated add-product route |

**Redirects to add in `next.config.ts` (or server-side):**

```
/auth/login  → /login
/auth/register → /register
/shops?q=*  → /search?q=*
/shops/*  → /shop/*
/checkout/*  → /orders/*
/dashboard  → /seller/dashboard
/dashboard/inventory  → /seller/inventory
/dashboard/shop-settings  → /seller/settings
/dashboard/onboarding  → /seller/onboarding
```

---

## Design System (from Design Project)

### Colors
```
--background: #F8FAFC (light) / #0F172A (dark)
--foreground: #111827 (light) / #F8FAFC (dark)
--primary:    #10B981 (emerald-500, same in dark)
--secondary:  #0F172A (light) / #334155 (dark)
--accent:     #F59E0B (amber-500)
--destructive: #EF4444 (red-500)
--muted:      #F1F5F9 (light) / #334155 (dark)
--muted-foreground: #6B7280 (light) / #94A3B8 (dark)
--border:     #E5E7EB (light) / #334155 (dark)
--ring:       #10B981
--radius:     0.75rem (12px)
```

Custom Ikobiz tokens:
```
--success: #22C55E
--warning: #F59E0B
--primary-hover: #059669
--primary-light: #D1FAE5
```

### Typography
- Font: **Inter** (via `next/font/google`, CSS variable `--font-inter`)
- Use `font-sans` class (maps to Inter via the CSS variable)

### Key Patterns
- Cards: `rounded-2xl border border-border bg-card p-6`
- Buttons primary: `bg-primary hover:bg-[#059669] text-primary-foreground`
- Spacing: standard Tailwind scale
- Icons: **lucide-react** throughout
- Dark mode: **next-themes** (ThemeProvider exists but not wired yet)

### UI Library
The design project includes **50+ shadcn/ui primitives** in `components/ui/`. Use these instead of raw HTML elements. Key ones already used:
- `Button`, `Input`, `Badge`, `Card`, `Label`
- `RadioGroup`, `Select`, `Tabs`, `Table`
- `DropdownMenu`, `Sheet`, `Dialog`
- `Avatar`, `Separator`, `Skeleton`
- `Toast` / `Toaster` / `Sonner` (for notifications)

### Files to Copy From Design Project
The following files should be copied from the design project into the functional project's `web/` directory:

**UI primitives:** `components/ui/` (entire directory)
**Shared components:** `components/navbar.tsx`, `components/footer.tsx`, `components/shop-card.tsx`, `components/product-card.tsx`, `components/theme-provider.tsx`
**Home sections:** `components/home/` (entire directory)
**Hooks:** `hooks/` (entire directory)
**Lib:** `lib/utils.ts`
**Public assets:** `public/` (any placeholder images needed)

**DO NOT copy:** `components.json`, `next.config.mjs`, `postcss.config.mjs`, `tsconfig.json`, `package.json`, `pnpm-lock.yaml` — these would overwrite the functional project's configuration.

### CSS
Merge the design project's `app/globals.css` CSS variable definitions (design tokens) into the functional project's `web/app/globals.css`. The functional project already has some CSS — integrate the design tokens without breaking existing class names.

---

## Functional Codebase — Critical Files to Understand

### API Layer
- `web/lib/api.ts` — `api.get/post/put/patch/del()` helpers, `formatPrice`, types (`Shop`, `Product`, `Order`, `CartItem`, `Message`)
- `web/lib/auth.tsx` — `AuthProvider`, `useAuth()` hook, login/register/logout, JWT token management in localStorage

### Existing Pages (to be redesigned)
Each page follows the same pattern: `"use client"`, `useEffect` to fetch data via `api.get()`, `useState` for data/loading, renders with existing CSS classes. All pages use `alert()` for feedback (replace with `sonner` toast).

### Navbar Auth Integration
The functional Navbar uses `useAuth()` to show login/register vs user menu, cart count from `GET /cart`. The design's Navbar has the right structure but uses hardcoded values. **The merged Navbar must use `useAuth()` and live API data.**

---

## Integration Order (recommended)

### Phase 1: Foundation
1. Copy UI primitives (`components/ui/`) into `web/components/ui/`
2. Copy hooks (`hooks/`) into `web/hooks/`
3. Copy `lib/utils.ts` to `web/lib/utils.ts`
4. Install missing npm packages (from design's `package.json`)
5. Merge `globals.css` — design tokens into functional project

### Phase 2: Shared Components
1. **Navbar** — merge design's navbar structure with functional navbar's auth/cart logic
2. **Footer** — adopt design's footer
3. **ShopCard, ProductCard** — adopt design's cards, wire to real API data types

### Phase 3: Homepage
1. Adopt design's homepage structure (HeroSection, FeaturedShops, PopularCategories, WhyIkobiz, WhatsAppFeature)
2. Wire FeaturedShops to real `GET /shops` data
3. Wire HeroSection search bar to navigate to `/search?q=...`

### Phase 4: Search / Browse
1. Convert `/search` from static to use `?q=` URL param
2. Wire to `GET /shops` and `GET /products` with client-side filtering
3. Integrate filter sidebar with real data

### Phase 5: Auth Pages
1. Redesign `/login` and `/register` with design's form layout
2. Wire to `api.post('/auth/login')` and `api.post('/auth/register')` from `lib/auth.tsx`
3. Add form validation with `react-hook-form` + `zod` (already in design's deps)

### Phase 6: Shop & Product Detail
1. Redesign `/shop/[id]` (or `/shop/[slug]`) with design's layout
2. Redesign `/product/[id]` with design's layout, quantity selector, add-to-cart, buy-now
3. Wire to real endpoints

### Phase 7: Cart & Checkout
1. Redesign `/cart` with design's layout + items table + promo code UI
2. Create new `/checkout` multi-step page (delivery → payment → confirm)
3. Wire both to real API calls

### Phase 8: Order Tracking
1. Create `/orders/[id]` with design's layout
2. Wire to real order data, status timeline, chat panel
3. Add cancel order functionality for cancellable statuses

### Phase 9: Seller Section
1. Adopt design's seller layout with sidebar
2. Redesign dashboard, inventory, orders, settings, onboarding pages
3. Wire to real seller API endpoints
4. **Add missing features** the design doesn't include but functional codebase has (see checklist below)

### Phase 10: Polish
1. Add `loading.tsx`, `error.tsx`, `not-found.tsx` at route level
2. Replace all `alert()` calls with `sonner` toast
3. Wire ThemeProvider into root layout
4. Add page redirects in `next.config.ts`
5. Remove `API_BASE` duplication — use single import from `lib/api.ts`

---

## Critical Checklist — Must Preserve / Add

### Auth & Session (must preserve)
- [ ] JWT token stored in `localStorage` as `ikobiz_token`
- [ ] User object stored as `ikobiz_user`
- [ ] `useAuth()` provides: `user`, `isLoggedIn`, `isSeller`, `login()`, `register()`, `logout()`, `refreshUser()`
- [ ] API calls pass auth flag to include Bearer token
- [ ] Role-based UI: sellers see Dashboard link, buyers see Orders link

### Cart (must preserve)
- [ ] `GET /cart` fetches from backend — not hardcoded
- [ ] Cart badge count in navbar is **live** from API, not hardcoded "2"
- [ ] Add to cart, remove item, update quantity all call API
- [ ] Cart shows "log in to view" for unauthenticated users

### Checkout (must preserve + expand)
- [ ] `POST /checkout` sends: `fulfillment_method`, `delivery_area`, `payment_method`, `customer_phone`
- [ ] Returns `{ order_id, total, status }` → redirect to `/orders/<id>`
- [ ] Design adds multi-step `/checkout` page — preserve the API contract

### Order Tracking (must preserve)
- [ ] `GET /orders` fetches real orders
- [ ] Status timeline shows real status (PENDING → CONFIRMED → DISPATCHED → DELIVERED)
- [ ] Chat loads real messages from `GET /orders/<id>/messages`
- [ ] Send message calls `POST /orders/<id>/messages`
- [ ] Cancel button appears for PENDING/CONFIRMED — calls `POST /orders/<id>/cancel`
- [ ] WhatsApp seller link with prefilled message

### Seller Dashboard (must preserve)
- [ ] `GET /dashboard/summary` shows real stats (shops, products, orders by status, revenue)
- [ ] `GET /seller/shop-orders` loads real orders
- [ ] Status dropdown updates via `PATCH /orders/<id>/status` with **transition validation**
- [ ] Per-order chat panel with real messages
- [ ] **Design's `/seller/orders` page must include inline chat per order row** (design may have dropped this)

### Seller Inventory (must preserve)
- [ ] `GET /seller/products` loads real products
- [ ] Add/edit product form with all fields: title, description, price, stock, category, attributes, image upload, status
- [ ] Image upload via `POST /upload/image` (Cloudinary) — **not** local file storage
- [ ] Delete product with confirmation
- [ ] **Design's inventory page lacks add/edit form** — must be added back

### Seller Settings (must preserve)
- [ ] `GET /seller/shops` loads shop data
- [ ] `PUT /shops/<id>` updates all fulfillment fields
- [ ] **Design's settings page is more comprehensive** — adopt the design but keep all functional fields

### Seller Onboarding (must preserve)
- [ ] Step-by-step wizard creates shop + first product
- [ ] All fulfillment fields collected
- [ ] Redirects to dashboard on completion

### Error & Loading States (must preserve from functional codebase)
- [ ] `.catch(() => {})` should be replaced with proper error handling (toast)
- [ ] Loading states during API calls
- [ ] Empty states for no data

---

## New Features from Design to Implement

| Feature | Priority | Notes |
|---------|----------|-------|
| Multi-step checkout page (`/checkout`) | High | Collects delivery address, contact info, payment method. Already backed by API |
| Popular Categories on homepage | Medium | Static data is fine (no backend endpoint for categories yet) |
| Why Ikobiz value props section | Low | Static marketing content |
| WhatsApp feature promo section | Low | Static marketing content |
| Promo code input in cart | Low | No backend support — UI only |
| Favorite/wishlist (heart icon) | Low | No backend support — UI only |
| Trust badges on product detail | Low | Static — add when backend supports |
| Related products section | Low | No backend endpoint — UI only |
| Top Products ranking on dashboard | Low | No backend endpoint — UI only |
| Hero stats (shops/products/customers) | Medium | Could be real from `GET /dashboard/summary` |
| Seller order detail page (`/seller/orders/[id]`) | Medium | New route — link from orders table |
| Add product page (`/seller/inventory/new`) | High | Design's inventory lacks add form — new page needed |
| Dark mode (next-themes) | Low | ThemeProvider exists, wire it in |
| Order timeline visualization | Medium | Replace text status with visual timeline |

---

## Critical Warnings

1. **NEVER remove or comment out existing API calls.** The design has zero API calls — every single endpoint call must be preserved and integrated into the new design's components.

2. **NEVER use hardcoded data for user-facing values.** The design uses mock arrays. Replace every mock with real API calls. The only exceptions are static marketing sections (Why Ikobiz, Popular Categories categories list, WhatsApp promo).

3. **Route redirects must be additive.** When adding new routes, add redirects from old routes to new routes. Never delete old route files until redirects are confirmed working.

4. **The design uses `[id]` for shop routes; the functional codebase uses `[slug]`.** The functional backend resolves `/ecobid/<slug>`. You must handle both `id` and `slug` in the shop detail page, or add a lookup endpoint. Best approach: keep the functional backend's slug-based lookup, make the design's numeric `id` links work via a resolver, and prefer `slug` in new links.

5. **Seller order management MUST include per-order chat.** The design's `/seller/orders` page has order actions but no inline chat. The functional codebase has per-order chat via `GET /orders/<id>/messages` and `POST /orders/<id>/messages`. This must be added back.

6. **Auth state drives the entire UI.** The Navbar, cart, seller sections, and protected routes all depend on `useAuth()`. Do not introduce a separate auth mechanism — use the existing `AuthProvider` from `lib/auth.tsx`.

7. **Replace `alert()` with `toast` from `sonner`.** The design project includes `sonner` as a dependency and has a `<Toaster />` component. Every existing `alert()` call should become `toast.success()` / `toast.error()`.

8. **Run `npm run build` (or relevant check) after each phase** to catch TypeScript errors early. The design project ignores TS errors in its config; the functional project must be strict.

---

## Verification Checklist (run after each phase)

- [ ] `npm run build` succeeds with no TypeScript errors
- [ ] All old routes redirect to new routes
- [ ] Auth flow works: register → login → see protected pages
- [ ] Cart loads from API when logged in
- [ ] Checkout creates real order → redirects to tracking
- [ ] Seller dashboard shows real data
- [ ] Navbar shows correct auth state (login/register vs user menu)
- [ ] Cart badge count is accurate
- [ ] No `alert()` calls remain
- [ ] Design colors and spacing are consistent across pages
- [ ] Mobile responsive: sidebar, navbar hamburger, grid layouts work
- [ ] Dark mode toggle works (after Phase 10)
