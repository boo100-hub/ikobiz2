"""
seed_pitch_demo.py - Seed data for pitch demo with founder story shops.

This creates 3 key shops matching the pitch story:
1. Grandma's Avocados (Mama Mboga story)
2. Greenhouse Tomatoes (Parents' story)
3. Chess & Games Store (Founder's story)

Run: python seed_pitch_demo.py
"""

from sqlalchemy import text
from core.database import SessionLocal
from core.security import hash_password
from models import User, Shop, Product, ProductStatus

# Clear all data
db = SessionLocal()
db.execute(text("TRUNCATE TABLE users CASCADE"))
db.commit()

# =====================================================================
# USERS
# =====================================================================

# Admin
admin = User(username="admin", email="admin@ikobiz.com", phone="254700000000", password_hash=hash_password("admin123"), role="admin")

# Demo Sellers (matching pitch story)
seller_grandma = User(username="grandma", email="grandma@ikobiz.com", phone="254714114994", password_hash=hash_password("seller123"), role="seller")
seller_greenhouse = User(username="greenhouse", email="greenhouse@ikobiz.com", phone="254108685345", password_hash=hash_password("seller123"), role="seller")
seller_chess = User(username="chess", email="chess@ikobiz.com", phone="254702193430", password_hash=hash_password("seller123"), role="seller")

# Demo Buyer
buyer = User(username="demo_buyer", email="demo@ikobiz.com", phone="254700000011", password_hash=hash_password("buyer123"), role="buyer")

db.add_all([admin, seller_grandma, seller_greenhouse, seller_chess, buyer])
db.commit()

# =====================================================================
# SHOPS - 3 story-matching shops
# =====================================================================

# Shop 1: Grandma's Avocados (Mama Mboga story)
shop_grandma = Shop(
    owner_id=seller_grandma.id,
    name="Grandma's Avocados",
    slug="grandmas-avocados",
    description="Fresh farm produce from my garden. I've been selling avocados and vegetables for 30 years. Quality you can trust!",
    banner_image="https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=800",
    category="food",
    location_area="Kawangware",
    location_gps_lat=-1.2867,
    location_gps_lng=36.7942,
    fulfillment_modes="pickup",
    delivery_radius_km=0,
    delivery_fee=0,
    operating_hours='{"mon-sat":"6:00-18:00","sun":"7:00-13:00"}',
    payment_methods="mpesa,cash",
    pickup_address="Kawangware Market, Stall 42, near Stage 42 matatu stop",
    phone="254714114994",
)

# Shop 2: Greenhouse Tomatoes (Parents' story)
shop_greenhouse = Shop(
    owner_id=seller_greenhouse.id,
    name="Greenhouse Tomatoes Kenya",
    slug="greenhouse-tomatoes-kenya",
    description="Premium greenhouse tomatoes and vegetables. Grown with care in our family greenhouse since 1995. Fresh, organic, and affordable.",
    banner_image="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800",
    category="food",
    location_area="Kiambu",
    location_gps_lat=-1.1733,
    location_gps_lng=36.8367,
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=15.0,
    delivery_fee=150,
    operating_hours='{"mon-fri":"7:00-17:00","sat":"7:00-14:00","sun":"closed"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Kiambu Road, 2km from Kiambu Town, next to Greenhouse Farm",
    phone="254108685345",
)

# Shop 3: Chess & Games Store (Founder's story)
shop_chess = Shop(
    owner_id=seller_chess.id,
    name="Chess & Games Store",
    slug="chess-games-store",
    description="Your destination for board games, chess sets, and family games. We believe games bring people together. Find your perfect game here!",
    banner_image="https://images.unsplash.com/photo-1529699211952-734e80c4d42b?w=800",
    category="games",
    location_area="Nairobi CBD",
    location_gps_lat=-1.2864,
    location_gps_lng=36.8172,
    fulfillment_modes="seller_delivery,pickup",
    delivery_radius_km=10.0,
    delivery_fee=200,
    operating_hours='{"mon-fri":"9:00-18:00","sat":"9:00-16:00","sun":"closed"}',
    payment_methods="mpesa,cash_on_delivery,bank_transfer",
    pickup_address="Biashara Street, City Market Building, Shop 15, Nairobi",
    phone="254702193430",
)

db.add_all([shop_grandma, shop_greenhouse, shop_chess])
db.commit()

# =====================================================================
# PRODUCTS
# =====================================================================

# Grandma's Avocados Products
products_grandma = [
    Product(
        shop_id=shop_grandma.id,
        title="Fresh Avocados (Hass)",
        description="Premium Hass avocados, freshly picked from my garden. Perfect for salads, sandwiches, or eating plain.",
        price=50,
        stock=100,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=400",
    ),
    Product(
        shop_id=shop_grandma.id,
        title="Fresh Tomatoes",
        description="Ripe, juicy tomatoes from local farmers. Great for cooking and salads.",
        price=30,
        stock=80,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400",
    ),
    Product(
        shop_id=shop_grandma.id,
        title="Fresh Kales (Sukuma Wiki)",
        description="Fresh sukuma wiki, harvested daily. A staple for every Kenyan home.",
        price=20,
        stock=60,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400",
    ),
    Product(
        shop_id=shop_grandma.id,
        title="Fresh Spinach",
        description="Organic spinach, rich in nutrients. Perfect for healthy meals.",
        price=25,
        stock=50,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400",
    ),
]

# Greenhouse Tomatoes Products
products_greenhouse = [
    Product(
        shop_id=shop_greenhouse.id,
        title="Greenhouse Tomatoes (Bulk)",
        description="Premium greenhouse tomatoes, grown in controlled environment. Perfect for restaurants and bulk buyers.",
        price=40,
        stock=200,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400",
    ),
    Product(
        shop_id=shop_greenhouse.id,
        title="Fresh Cucumbers",
        description="Crisp, fresh cucumbers from our greenhouse. Great for salads and healthy snacks.",
        price=35,
        stock=80,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1589621316382-008455b857cd?w=400",
    ),
    Product(
        shop_id=shop_greenhouse.id,
        title="Bell Peppers (Mixed)",
        description="Colorful bell peppers - red, green, and yellow. Fresh from our greenhouse.",
        price=45,
        stock=60,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=400",
    ),
]

# Chess & Games Store Products
products_chess = [
    Product(
        shop_id=shop_chess.id,
        title="Chess Board (Wooden)",
        description="Premium wooden chess board with handcrafted pieces. Perfect for beginners and experts alike.",
        price=2500,
        stock=15,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=400",
    ),
    Product(
        shop_id=shop_chess.id,
        title="Chess Board (Magnetic)",
        description="Travel-friendly magnetic chess board. Play anywhere, anytime.",
        price=800,
        stock=25,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=400",
    ),
    Product(
        shop_id=shop_chess.id,
        title="Scrabble Board Game",
        description="Classic word game. Build vocabulary and have fun with family and friends.",
        price=1500,
        stock=18,
        status=ProductStatus.ACTIVE,
        image_url="https://images.unsplash.com/photo-1486769050672-2d5e0f34bd2e?w=400",
    ),
]

db.add_all(products_grandma + products_greenhouse + products_chess)
db.commit()

db.close()

print("Pitch demo database seeded successfully!")
print(f"  - 3 story-matching shops created:")
print(f"    1. Grandma's Avocados (Kawangware)")
print(f"    2. Greenhouse Tomatoes Kenya (Kiambu)")
print(f"    3. Chess & Games Store (Nairobi CBD)")
print(f"  - {len(products_grandma + products_greenhouse + products_chess)} products created")
print(f"\nDemo queries to test:")
print(f'  - "Where can I buy avocados?"')
print(f'  - "I need a chess board"')
print(f'  - "Where can I find tomatoes?"')
print(f'  - "Show me fresh vegetables"')
