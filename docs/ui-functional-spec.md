# Ikobiz Marketplace — UI Functional Specification

## Product Description

**Ikobiz Marketplace** is a dual-channel (web + WhatsApp) local commerce platform connecting buyers and sellers in Kenya. Sellers register, set up shops, list products, and manage orders through a web dashboard. Buyers discover shops and products, add to cart, and place orders via the web or through a WhatsApp AI assistant. The platform handles the full order lifecycle: discovery → cart/checkout → payment → fulfillment tracking → seller notification.

**Target users:**
- **Buyers** — browse shops/products, add to cart, place orders, track fulfillment
- **Sellers** — onboard, manage shop settings, add/edit products, receive/fulfill orders via dashboard

**Key constraints:** Mobile-first (many users on phones), simple and fast (emerging market), works alongside WhatsApp channel.

---

## Pages — Functional Description

### 1. Homepage (`/`)

**Purpose:** Main landing page. Lets users search or discover featured shops.

**Data:**
- Fetch all shops via `GET /shops` (id, name, slug, description, banner_image, location_area)
- Search query from search bar

**User actions:**
- Type in search bar and submit → navigate to `/shops?q=<query>`
- Click a shop card → navigate to `/shops/<slug>`

**Components needed:**
- **SearchBar** — text input + submit button, fires navigation to search results
- **ShopCard** — displays shop banner image, name, description snippet, location. Entire card is a link to `/shops/<slug>`
- **FeaturedShopsGrid** — responsive grid of ShopCard components
- **HeroSection** — welcome heading, tagline, search bar

---

### 2. Shop Search Results (`/shops?q=<query>`)

**Purpose:** Display shops and products matching the search query.

**Data:**
- Read `?q=` from URL params
- Fetch `GET /shops` and `GET /products`, filter client-side by name/description match

**User actions:**
- See matching shops and products grouped separately
- Click a shop card → `/shops/<slug>`
- Click a product card → `/product/<id>`

**Components needed:**
- **SearchResultsHeader** — heading showing query and result count
- **ShopCard** (shared) — same as homepage
- **ProductCard** (shared) — displays product image, title, shop name, price, stock badge
- **ResultsGrid** — responsive grid, shops section then products section
- **EmptyState** — message when no results found

---

### 3. Shop Detail (`/shops/[slug]`)

**Purpose:** Show a single shop's profile and its products.

**Data:**
- `GET /ecobid/<slug>` — shop info (name, description, banner_image, location_area, fulfillment_modes, delivery_radius_km, delivery_fee, operating_hours, payment_methods, pickup_address, phone, category)
- `GET /shops/<id>/products` — list of products in this shop

**User actions:**
- Browse products listed by this shop
- Click a product → `/product/<id>`
- See shop fulfillment/pickup/payment info

**Components needed:**
- **ShopHeader** — banner image, shop name, category, description, location
- **FulfillmentInfo** — section showing delivery modes, delivery fee, pickup address, operating hours, payment methods, phone. May be collapsed by default
- **ProductCard** (shared) — product grid for this shop's products
- **WhatsAppContactButton** — link to `wa.me/<shop_phone>` for direct contact

---

### 4. Product Detail (`/product/[id]`)

**Purpose:** Show product info and allow add-to-cart or instant buy.

**Data:**
- `GET /products/<id>` — product (id, title, description, price, stock, image_url, category, attributes, shop_name, shop_slug, shop_id)

**User actions:**
- View product image, title, price, description, category, stock status
- Select quantity (dropdown 1–stock, capped at 10)
- Click "Add to Cart" → `POST /cart/add` with product_id, quantity
- Click "Buy Now" → `POST /checkout` → navigate to `/checkout/<order_id>`
- See "Out of Stock" state when stock = 0

**Components needed:**
- **ProductImage** — main product image with fallback placeholder
- **ProductInfo** — title, price, description, category, attributes
- **StockBadge** — shows "In Stock", "Only X left", or "Out of Stock" with color indication
- **QuantitySelector** — dropdown number picker
- **AddToCartButton** — triggers add to cart API, shows success/error feedback
- **BuyNowButton** — triggers checkout API, navigates to order tracking
- **ShopLink** — link back to `/shops/<shop_slug>`

---

### 5. Cart + Checkout (`/cart`)

**Purpose:** View cart items, set delivery preferences, place order.

**Data:**
- `GET /cart` (auth required) — cart items (id, quantity, product.id, product.title, product.price, product.image_url, product.shop_name)
- User profile from auth context (username, phone)

**User actions:**
- View cart items in a table/list: image, title, unit price, quantity, line total
- Remove individual items → `DELETE /cart/<item_id>`
- Choose delivery method (radio): "Deliver to me" or "Pickup from shop"
- If delivery: enter delivery area text (e.g. "Rongai near Quickmart")
- Choose payment method (radio): "Cash on Delivery" or "M-Pesa"
- Enter phone number for contact (pre-filled from user profile)
- Click "Place Order" → `POST /checkout` with fulfillment_method, delivery_area, payment_method, customer_phone → navigate to `/checkout/<order_id>`

**Components needed:**
- **CartItemRow** — image, title, unit price, quantity, line total, remove button
- **CartTable** — header row + list of CartItemRows, totals
- **EmptyCart** — message + "Browse Shops" link when cart is empty
- **CheckoutForm** — card/panel containing:
  - Delivery method radio group
  - Delivery area text input (conditional on delivery method)
  - Payment method radio group
  - Phone input
- **TotalBar** — shows cart total + Place Order button

---

### 6. Order Tracking (`/checkout/[id]`)

**Purpose:** Show order status, fulfillment details, and buyer-seller messaging.

**Data:**
- `GET /orders` (auth required, filtered client-side or by id) — order (id, total, status, created_at, items[], fulfillment_method, delivery_area, delivery_fee, payment_method, payment_status, customer_name, customer_phone, seller_notes)
- `GET /orders/<id>/messages` — chat messages (id, sender_name, content, is_auto_reply, created_at)

**User actions:**
- View order status with timeline/progress
- See order summary (items, totals, delivery info, payment method)
- Send a message to the seller → `POST /orders/<id>/messages`
- Cancel order if status is PENDING or CONFIRMED → `POST /orders/<id>/cancel`

**Components needed:**
- **OrderStatusTimeline** — visual progress through PENDING → CONFIRMED → DISPATCHED → DELIVERED (or CANCELLED). Current status highlighted
- **OrderSummaryCard** — order id, date, items list (image + title + qty + price), subtotal, delivery fee, total, fulfillment method, delivery area, payment method, payment status
- **ChatPanel** — message list (auto-replies styled differently) + text input + send button
- **CancelOrderButton** — shown only when cancellable (PENDING/CONFIRMED), triggers confirmation then API call
- **WhatsAppSellerLink** — `wa.me` link to contact seller directly

---

### 7. Auth — Login (`/auth/login`)

**Purpose:** User login.

**Data:** None (form input)

**User actions:**
- Enter username + password
- Submit → `POST /auth/login` → store token → redirect to `/`
- Link to registration page

**Components needed:**
- **LoginForm** — username input, password input, submit button
- **AuthLink** — "Don't have an account? Sign Up" link to `/auth/register`

---

### 8. Auth — Register (`/auth/register`)

**Purpose:** New user registration with optional seller account.

**Data:** None (form input)

**User actions:**
- Enter username, email, password, phone number
- Check "Register as seller" checkbox
- Submit → `POST /auth/register` → auto-login → redirect to `/`
- Link to login page

**Components needed:**
- **RegisterForm** — username input, email input, password input, phone input, seller checkbox, submit button
- **AuthLink** — "Already have an account? Login" link to `/auth/login`

---

### 9. Seller Dashboard — Overview (`/dashboard`)

**Purpose:** Seller's command center — see recent orders, update status, chat with buyers.

**Data:**
- `GET /seller/shop-orders` (auth required, seller role) — orders with items, buyer info, fulfillment details
- `GET /dashboard/summary` — total shops, products, orders by status, total revenue

**User actions:**
- View summary stats (orders by status, revenue)
- View recent orders table with status, items, buyer, total, date
- Update order status via dropdown (PENDING→CONFIRMED→DISPATCHED→DELIVERED) → `PATCH /orders/<id>/status`
- Send messages to buyer for a specific order → `POST /orders/<id>/messages`
- Click into order row to view details and chat

**Components needed:**
- **DashboardSummaryCards** — stat cards showing total orders, pending orders, confirmed, dispatched, delivered, total revenue
- **OrdersTable** — table with columns: order ID, buyer name, items summary, total, status, date, actions. Each row has a status dropdown and a "Chat" button
- **StatusDropdown** — inline dropdown to change order status (validated against transition rules)
- **InlineChatModal** — modal/panel showing order chat + message input

---

### 10. Seller Dashboard — Inventory (`/dashboard/inventory`)

**Purpose:** Manage products — add, edit, delete, update stock/status.

**Data:**
- `GET /seller/products` (auth, seller) — list of seller's products
- `GET /seller/shops` (auth, seller) — seller's shops (needed to assign new products)
- `POST /upload/image` — upload to Cloudinary

**User actions:**
- View all products in a table: image, title, price, stock, status, shop
- Add new product → expand form with shop selector, title, description, price, stock, category, attributes, image upload, status
- Edit existing product → pre-filled form same as add
- Delete product → confirm then `DELETE /products/<id>`
- Toggle product status (ACTIVE/HIDDEN/OUT_OF_STOCK)

**Components needed:**
- **ProductTable** — table with product info + action buttons (edit, delete, status toggle)
- **ProductForm** — form with fields: shop_id (dropdown), title, description, price, stock, category (dropdown), attributes (text), image upload (file input → Cloudinary → stores URL), status (dropdown). Used for both add and edit
- **ImageUploader** — file input that uploads to `POST /upload/image` and returns the URL
- **EmptyInventory** — message when no products + "Add Product" CTA

---

### 11. Seller Dashboard — Shop Settings (`/dashboard/shop-settings`)

**Purpose:** Edit shop profile and fulfillment configuration.

**Data:**
- `GET /seller/shops` (auth, seller) — shop list
- `PUT /shops/<id>` — update shop

**User actions:**
- Select which shop to edit (if seller has multiple)
- Update: name, description, category, location_area, fulfillment_modes, delivery_radius_km, delivery_fee, operating_hours, payment_methods, pickup_address, phone, banner_image

**Components needed:**
- **ShopSelector** — dropdown to pick which shop to edit
- **ShopSettingsForm** — form with all shop fields:
  - Text inputs: name, description, location_area, delivery_radius_km, delivery_fee, operating_hours, pickup_address, phone
  - Dropdowns: category, fulfillment_modes (multi-select or comma-separated), payment_methods
  - Image upload: banner image
- **ImageUploader** (shared)

---

### 12. Seller Dashboard — Onboarding (`/dashboard/onboarding`)

**Purpose:** Step-by-step wizard for new sellers to set up their shop.

**Data:** None initially, creates via `POST /shops`

**Steps:**
1. **Shop basics** — name, description, category, location area
2. **Fulfillment setup** — delivery method, delivery radius, delivery fee, operating hours, pickup address
3. **Payment setup** — payment methods accepted, phone number
4. **First product** — add initial product (title, description, price, stock, image)

**User actions:**
- Navigate through steps (next/back)
- Each step saves to a pending shop object
- On final step, creates shop + first product via API
- Redirects to dashboard on completion

**Components needed:**
- **StepIndicator** — shows current step out of total (1/4, 2/4, etc.)
- **StepContent** — renders the form for the current step
- **NavigationButtons** — Back / Next / Finish
- **ShopBasicsForm** — name, description, category dropdown, location area
- **FulfillmentForm** — fulfillment_modes, delivery_radius_km, delivery_fee, operating_hours, pickup_address
- **PaymentForm** — phone, payment_methods
- **FirstProductForm** — title, description, price, stock, image upload

---

## Shared/Global Components

These appear across multiple pages:

| Component | Used On | Function |
|---|---|---|
| **Navbar** | All pages | Brand logo, search bar with Enter-to-search, cart icon with count badge, dashboard link (sellers), login/signup links (guests), username + logout (logged in) |
| **Footer** | All pages | Brand, copyright, WhatsApp contact link |
| **ShopCard** | Homepage, Search Results | Banner image, shop name, description, location. Card is a link to `/shops/<slug>` |
| **ProductCard** | Search Results, Shop Detail, Dashboard | Product image, title, shop name, price, stock badge. Card is a link to `/product/<id>` |
| **LoadingSpinner** | All data-fetching pages | Centered spinner shown while API calls are in flight |
| **ErrorBoundary** | All routes | Fallback UI when a component crashes |
| **Toast/Notification** | Cart, Checkout, Dashboard | Non-blocking success/error messages (replacing `alert()`) |
| **ImageUploader** | Inventory, Shop Settings, Onboarding | File input → upload to Cloudinary → return URL |

## API Endpoints Reference (for component data needs)

| Method | Path | Auth | Returns |
|---|---|---|---|
| GET | /shops | No | Shop[] |
| GET | /ecobid/{slug} | No | Shop detail |
| GET | /products | No | Product[] |
| GET | /products/{id} | No | Product detail |
| GET | /shops/{id}/products | No | Product[] |
| POST | /cart/add | Yes | CartItem |
| DELETE | /cart/{id} | Yes | 200 |
| GET | /cart | Yes | CartItem[] |
| POST | /checkout | Yes | {order_id, total, status} |
| GET | /orders | Yes | Order[] |
| PATCH | /orders/{id}/status | Yes (seller) | OrderStatusUpdateResponse |
| POST | /orders/{id}/cancel | Yes (buyer) | {status, message} |
| GET | /orders/{id}/messages | Yes | Message[] |
| POST | /orders/{id}/messages | Yes | Message |
| GET | /dashboard/summary | Yes (seller) | Dashboard summary |
| GET | /seller/shop-orders | Yes (seller) | Order[] |
| GET | /seller/products | Yes (seller) | Product[] |
| GET | /seller/shops | Yes (seller) | Shop[] |
| POST | /shops | Yes (seller) | Shop |
| PUT | /shops/{id} | Yes (seller) | Shop |
| DELETE | /shops/{id} | Yes (seller) | 204 |
| POST | /shops/{id}/products | Yes (seller) | Product |
| PUT | /products/{id} | Yes (seller) | Product |
| DELETE | /products/{id} | Yes (seller) | 204 |
| POST | /upload/image | Yes | {url} |
| POST | /auth/register | No | User |
| POST | /auth/login | No | {access_token} |
| GET | /auth/me | Yes | User |
