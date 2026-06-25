"""
seed.py - Populates the database with sample data.

Run: python seed.py
"""

from core.database import SessionLocal
from core.security import hash_password
from models import User, Shop, Product, ProductStatus

db = SessionLocal()

# =====================================================================
# USERS
# =====================================================================

admin = User(username="admin", email="admin@ikobiz.com", phone="254700000000", password_hash=hash_password("admin123"), role="admin")
alice = User(username="alice", email="alice@ikobiz.com", phone="254700000001", password_hash=hash_password("seller123"), role="seller")
bob = User(username="bob", email="bob@ikobiz.com", phone="254700000002", password_hash=hash_password("seller123"), role="seller")
diana = User(username="diana", email="diana@ikobiz.com", phone="254700000003", password_hash=hash_password("seller123"), role="seller")
eve = User(username="eve", email="eve@ikobiz.com", phone="254700000004", password_hash=hash_password("buyer123"), role="buyer")
frank = User(username="frank", email="frank@ikobiz.com", phone="254700000005", password_hash=hash_password("buyer123"), role="buyer")

db.add_all([admin, alice, bob, diana, eve, frank])
db.commit()

# =====================================================================
# PRIMARY MARKET — shops
# =====================================================================

shop1 = Shop(
    owner_id=alice.id, name="Mama Mboga", slug="mama-mboga",
    description="Fresh farm produce delivered daily. Fruits, vegetables, and organic goods straight from the farm.",
    banner_image="https://images.unsplash.com/photo-1542838132-92c53300491e?w=800",
    category="food",
    location_area="Kawangware",
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=5.0,
    delivery_fee=100,
    operating_hours='{"mon-fri":"7:00-19:00","sat":"7:00-17:00","sun":"8:00-14:00"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Kawangware Market, Stage 42, Nairobi",
    phone="254700000001",
)

shop2 = Shop(
    owner_id=bob.id, name="Tech Store", slug="tech-store",
    description="Gadgets, accessories, and electronics at affordable prices. From phone cases to laptops.",
    banner_image="https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800",
    category="electronics",
    location_area="Westlands",
    fulfillment_modes="seller_delivery",
    delivery_radius_km=10.0,
    delivery_fee=250,
    operating_hours='{"mon-fri":"9:00-20:00","sat":"9:00-18:00","sun":"closed"}',
    payment_methods="mpesa,cash_on_delivery,bank_transfer",
    pickup_address="Westlands Shopping Centre, 2nd Floor, Nairobi",
    phone="254700000002",
)

shop3 = Shop(
    owner_id=diana.id, name="Shoe Palace", slug="shoe-palace",
    description="Sneakers, boots, sandals, and more. Trendy footwear for every occasion.",
    banner_image="https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=800",
    category="fashion",
    location_area="CBD",
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=8.0,
    delivery_fee=200,
    operating_hours='{"mon-fri":"8:00-19:00","sat":"8:00-17:00","sun":"10:00-15:00"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Moi Avenue, Ambassador Building, G4, Nairobi",
    phone="254700000003",
)

db.add_all([shop1, shop2, shop3])
db.commit()

# =====================================================================
# PRIMARY MARKET — products
# =====================================================================

prods = [
    Product(shop_id=shop1.id, title="Organic Tomatoes (1kg)", description="Ripe, juicy tomatoes straight from the farm.", price=150, stock=50, category="vegetables", image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400"),
    Product(shop_id=shop1.id, title="Fresh Kale (1 bunch)", description="Crisp green kale, perfect for sukuma wiki.", price=80, stock=80, category="vegetables", image_url="https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400"),
    Product(shop_id=shop1.id, title="Ripe Bananas (1 bunch)", description="Sweet yellow bananas, great for snacking.", price=120, stock=60, category="fruits", image_url="https://images.unsplash.com/photo-1571771894821-ce9b6c11b08d?w=400"),
    Product(shop_id=shop1.id, title="Fresh Milk (1L)", description="Fresh whole milk from smallholder farmers.", price=70, stock=40, category="dairy", image_url="https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400"),
    Product(shop_id=shop1.id, title="Brown Eggs (tray of 30)", description="Farm-fresh brown eggs, rich in flavor.", price=350, stock=25, category="dairy", image_url="https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400"),
    Product(shop_id=shop2.id, title="Wireless Bluetooth Earbuds", description="Compact earbuds with noise cancellation and 8h battery.", price=2500, stock=30, category="audio", attributes='{"color":"black"}', image_url="https://images.unsplash.com/photo-1590658268037-6bf12f032f55?w=400"),
    Product(shop_id=shop2.id, title="USB-C Hub 7-in-1", description="Multi-port adapter with HDMI, USB 3.0, SD card reader.", price=1800, stock=40, category="accessories", image_url="https://images.unsplash.com/photo-1547394765-185e1e68f34e?w=400"),
    Product(shop_id=shop2.id, title="Phone Stand Adjustable", description="Aluminum adjustable stand for desk or bedside.", price=1200, stock=25, category="accessories", image_url="https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400"),
    Product(shop_id=shop2.id, title="64GB USB Flash Drive", description="High-speed USB 3.0 flash drive. Plug and play.", price=1500, stock=50, category="storage", image_url="https://images.unsplash.com/photo-1618410320928-25228d811631?w=400"),
    Product(shop_id=shop2.id, title="Bluetooth Speaker", description="Portable speaker with deep bass. 12h battery life.", price=3500, stock=20, category="audio", attributes='{"color":"blue"}', image_url="https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400"),
    Product(shop_id=shop3.id, title="Classic White Sneakers", description="Timeless white sneakers, comfortable and durable.", price=4500, stock=20, category="shoes", attributes='{"color":"white","size":"42"}', image_url="https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400"),
    Product(shop_id=shop3.id, title="Leather Ankle Boots", description="Stylish brown leather boots for men and women.", price=6500, stock=15, category="shoes", attributes='{"color":"brown","size":"43"}', image_url="https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400"),
    Product(shop_id=shop3.id, title="Slip-on Sandals", description="Lightweight summer sandals with cushioned sole.", price=2200, stock=35, category="shoes", attributes='{"color":"black","size":"41"}', image_url="https://images.unsplash.com/photo-1603487742131-4160ec999306?w=400"),
    Product(shop_id=shop3.id, title="Running Shoes", description="Breathable mesh running shoes with cushioned sole.", price=5500, stock=18, category="shoes", attributes='{"color":"blue","size":"44"}', image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"),
]
db.add_all(prods)
db.commit()

db.close()

print("Database seeded successfully!")
print(f"  - {6} users (admin, 3 sellers, 2 buyers)")
print(f"  - {3} shops created")
print(f"  - {len(prods)} primary products created")
print()
print("Test accounts:")
print("  admin / admin123  (full access)")
print("  alice / seller123 (owns Mama Mboga — Kawangware)")
print("  bob   / seller123 (owns Tech Store — Westlands)")
print("  diana / seller123 (owns Shoe Palace — CBD)")
print("  eve   / buyer123  (buyer)")
print("  frank / buyer123  (buyer)")
