"""
seed_comprehensive.py - Comprehensive seed data with 10 diverse shops and users.

Run: python seed_comprehensive.py
"""

from sqlalchemy import text
from core.database import SessionLocal, engine
from core.security import hash_password
from models import User, Shop, Product, ProductStatus

# Clear all data
db = SessionLocal()

# Clear all data using TRUNCATE CASCADE which handles all related tables
db.execute(text("TRUNCATE TABLE users CASCADE"))
db.commit()

# =====================================================================
# USERS
# =====================================================================

# Admin
admin = User(username="admin", email="admin@ikobiz.com", phone="254700000000", password_hash=hash_password("admin123"), role="admin")

# Sellers (10 shop owners)
seller1 = User(username="john", email="john@ikobiz.com", phone="254714114994", password_hash=hash_password("seller123"), role="seller")
seller2 = User(username="mary", email="mary@ikobiz.com", phone="254108685345", password_hash=hash_password("seller123"), role="seller")
seller3 = User(username="peter", email="peter@ikobiz.com", phone="254702193430", password_hash=hash_password("seller123"), role="seller")
seller4 = User(username="grace", email="grace@ikobiz.com", phone="254700000004", password_hash=hash_password("seller123"), role="seller")
seller5 = User(username="david", email="david@ikobiz.com", phone="254700000005", password_hash=hash_password("seller123"), role="seller")
seller6 = User(username="susan", email="susan@ikobiz.com", phone="254700000006", password_hash=hash_password("seller123"), role="seller")
seller7 = User(username="james", email="james@ikobiz.com", phone="254700000007", password_hash=hash_password("seller123"), role="seller")
seller8 = User(username="hannah", email="hannah@ikobiz.com", phone="254700000008", password_hash=hash_password("seller123"), role="seller")
seller9 = User(username="robert", email="robert@ikobiz.com", phone="254700000009", password_hash=hash_password("seller123"), role="seller")
seller10 = User(username="esther", email="esther@ikobiz.com", phone="254700000010", password_hash=hash_password("seller123"), role="seller")

# Buyers
buyer1 = User(username="alice", email="alice@ikobiz.com", phone="254700000011", password_hash=hash_password("buyer123"), role="buyer")
buyer2 = User(username="bob", email="bob@ikobiz.com", phone="254700000012", password_hash=hash_password("buyer123"), role="buyer")
buyer3 = User(username="charles", email="charles@ikobiz.com", phone="254700000013", password_hash=hash_password("buyer123"), role="buyer")

db.add_all([admin, seller1, seller2, seller3, seller4, seller5, seller6, seller7, seller8, seller9, seller10, buyer1, buyer2, buyer3])
db.commit()

# =====================================================================
# SHOPS - 10 diverse shops across different categories
# =====================================================================

# Shop 1: Food & Groceries
shop1 = Shop(
    owner_id=seller1.id,
    name="Fresh Market Kenya",
    slug="fresh-market-kenya",
    description="Your one-stop shop for fresh farm produce, groceries, and organic foods. We source directly from local farmers.",
    banner_image="https://images.unsplash.com/photo-1542838132-92c53300491e?w=800",
    category="food",
    location_area="Kawangware",
    location_gps_lat=-1.2867,
    location_gps_lng=36.7942,
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=5.0,
    delivery_fee=100,
    operating_hours='{"mon-fri":"7:00-19:00","sat":"7:00-17:00","sun":"8:00-14:00"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Kawangware Market, Stage 42, Nairobi",
    phone="254714114994",
)

# Shop 2: Electronics
shop2 = Shop(
    owner_id=seller2.id,
    name="Tech Galaxy Kenya",
    slug="tech-galaxy-kenya",
    description="Premium electronics store offering the latest gadgets, phones, laptops, and accessories with warranty.",
    banner_image="https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800",
    category="electronics",
    location_area="Westlands",
    location_gps_lat=-1.2296,
    location_gps_lng=36.8167,
    fulfillment_modes="seller_delivery,pickup",
    delivery_radius_km=10.0,
    delivery_fee=250,
    operating_hours='{"mon-fri":"9:00-20:00","sat":"9:00-18:00","sun":"closed"}',
    payment_methods="mpesa,cash_on_delivery,bank_transfer",
    pickup_address="Westlands Shopping Centre, 2nd Floor, Nairobi",
    phone="254108685345",
)

# Shop 3: Fashion & Clothing
shop3 = Shop(
    owner_id=seller3.id,
    name="Style Hub Fashion",
    slug="style-hub-fashion",
    description="Trendy fashion store offering the latest clothing, shoes, and accessories for men and women.",
    banner_image="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800",
    category="fashion",
    location_area="CBD",
    location_gps_lat=-1.2864,
    location_gps_lng=36.8172,
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=8.0,
    delivery_fee=200,
    operating_hours='{"mon-fri":"8:00-19:00","sat":"8:00-17:00","sun":"10:00-15:00"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Moi Avenue, Ambassador Building, G4, Nairobi",
    phone="254702193430",
)

# Shop 4: Home & Furniture
shop4 = Shop(
    owner_id=seller4.id,
    name="Home Comforts Kenya",
    slug="home-comforts-kenya",
    description="Quality home furniture, decor, and household items to make your living space beautiful and comfortable.",
    banner_image="https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?w=800",
    category="home",
    location_area="Karen",
    location_gps_lat=-1.3176,
    location_gps_lng=36.8108,
    fulfillment_modes="seller_delivery",
    delivery_radius_km=15.0,
    delivery_fee=500,
    operating_hours='{"mon-fri":"9:00-18:00","sat":"9:00-16:00","sun":"closed"}',
    payment_methods="mpesa,cash_on_delivery,bank_transfer",
    pickup_address="Karen Shopping Mall, Shop 12, Nairobi",
    phone="254700000004",
)

# Shop 5: Beauty & Cosmetics
shop5 = Shop(
    owner_id=seller5.id,
    name="Glow Beauty Store",
    slug="glow-beauty-store",
    description="Premium beauty products, cosmetics, skincare, and hair care products from top brands.",
    banner_image="https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=800",
    category="beauty",
    location_area="Kilimani",
    location_gps_lat=-1.2738,
    location_gps_lng=36.8112,
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=7.0,
    delivery_fee=150,
    operating_hours='{"mon-fri":"9:00-20:00","sat":"9:00-18:00","sun":"11:00-16:00"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Kilimani Plaza, Ground Floor, Nairobi",
    phone="254700000005",
)

# Shop 6: Sports & Fitness
shop6 = Shop(
    owner_id=seller6.id,
    name="FitLife Sports Kenya",
    slug="fitlife-sports-kenya",
    description="Sports equipment, fitness gear, gym accessories, and athletic wear for all your fitness needs.",
    banner_image="https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800",
    category="sports",
    location_area="Lavington",
    location_gps_lat=-1.2655,
    location_gps_lng=36.8085,
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=10.0,
    delivery_fee=200,
    operating_hours='{"mon-fri":"8:00-19:00","sat":"8:00-17:00","sun":"9:00-14:00"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Lavington Green, Shop 5, Nairobi",
    phone="254700000006",
)

# Shop 7: Books & Stationery
shop7 = Shop(
    owner_id=seller7.id,
    name="Bookworm Kenya",
    slug="bookworm-kenya",
    description="Wide selection of books, educational materials, stationery, and office supplies for students and professionals.",
    banner_image="https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=800",
    category="books",
    location_area="Nairobi CBD",
    location_gps_lat=-1.2864,
    location_gps_lng=36.8172,
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=5.0,
    delivery_fee=100,
    operating_hours='{"mon-fri":"8:00-18:00","sat":"9:00-16:00","sun":"closed"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Kenya Cinema Plaza, 1st Floor, Nairobi",
    phone="254700000007",
)

# Shop 8: Automotive
shop8 = Shop(
    owner_id=seller8.id,
    name="AutoParts Kenya",
    slug="autoparts-kenya",
    description="Quality car parts, accessories, and automotive supplies for all vehicle makes and models.",
    banner_image="https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=800",
    category="automotive",
    location_area="Industrial Area",
    location_gps_lat=-1.2921,
    location_gps_lng=36.8359,
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=12.0,
    delivery_fee=300,
    operating_hours='{"mon-fri":"8:00-17:00","sat":"8:00-13:00","sun":"closed"}',
    payment_methods="mpesa,cash_on_delivery,bank_transfer",
    pickup_address="Industrial Area, Enterprise Road, Nairobi",
    phone="254700000008",
)

# Shop 9: Health & Wellness
shop9 = Shop(
    owner_id=seller9.id,
    name="Wellness Hub Kenya",
    slug="wellness-hub-kenya",
    description="Health supplements, vitamins, wellness products, and natural remedies for a healthy lifestyle.",
    banner_image="https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800",
    category="health",
    location_area="Hurlingham",
    location_gps_lat=-1.2833,
    location_gps_lng=36.8056,
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=8.0,
    delivery_fee=150,
    operating_hours='{"mon-fri":"9:00-19:00","sat":"9:00-17:00","sun":"10:00-14:00"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Hurlingham Shopping Centre, Nairobi",
    phone="254700000009",
)

# Shop 10: Pets & Pet Supplies
shop10 = Shop(
    owner_id=seller10.id,
    name="Pet Paradise Kenya",
    slug="pet-paradise-kenya",
    description="Complete pet store offering pet food, accessories, toys, and supplies for dogs, cats, and other pets.",
    banner_image="https://images.unsplash.com/photo-1450778869180-41d0601e046e?w=800",
    category="pets",
    location_area="Kileleshwa",
    location_gps_lat=-1.2619,
    location_gps_lng=36.8033,
    fulfillment_modes="pickup,seller_delivery",
    delivery_radius_km=6.0,
    delivery_fee=120,
    operating_hours='{"mon-fri":"8:00-19:00","sat":"8:00-17:00","sun":"10:00-15:00"}',
    payment_methods="mpesa,cash_on_delivery",
    pickup_address="Kileleshwa Mall, Shop 8, Nairobi",
    phone="254700000010",
)

db.add_all([shop1, shop2, shop3, shop4, shop5, shop6, shop7, shop8, shop9, shop10])
db.commit()

# =====================================================================
# PRODUCTS
# =====================================================================

prods = [
    # Fresh Market Kenya - Food & Groceries
    Product(shop_id=shop1.id, title="Organic Tomatoes (1kg)", description="Ripe, juicy tomatoes straight from the farm.", price=150, stock=50, category="vegetables", image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400"),
    Product(shop_id=shop1.id, title="Fresh Kale (1 bunch)", description="Crisp green kale, perfect for sukuma wiki.", price=80, stock=80, category="vegetables", image_url="https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400"),
    Product(shop_id=shop1.id, title="Ripe Bananas (1 bunch)", description="Sweet yellow bananas, great for snacking.", price=120, stock=60, category="fruits", image_url="https://images.unsplash.com/photo-1571771894821-ce9b6c11b08d?w=400"),
    Product(shop_id=shop1.id, title="Fresh Mangoes (1kg)", description="Sweet Kenyan mangoes, seasonal and delicious.", price=200, stock=40, category="fruits", image_url="https://images.unsplash.com/photo-1553279768-865429fa0078?w=400"),
    Product(shop_id=shop1.id, title="Fresh Milk (1L)", description="Fresh whole milk from smallholder farmers.", price=70, stock=40, category="dairy", image_url="https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400"),
    Product(shop_id=shop1.id, title="Brown Eggs (tray of 30)", description="Farm-fresh brown eggs, rich in flavor.", price=350, stock=25, category="dairy", image_url="https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400"),

    # Tech Galaxy Kenya - Electronics
    Product(shop_id=shop2.id, title="Wireless Bluetooth Earbuds", description="Compact earbuds with noise cancellation and 8h battery.", price=2500, stock=30, category="audio", attributes='{"color":"black"}', image_url="https://images.unsplash.com/photo-1590658268037-6bf12f032f55?w=400"),
    Product(shop_id=shop2.id, title="Wireless Mouse", description="Ergonomic wireless mouse with silent clicks and long battery life.", price=1500, stock=45, category="accessories", image_url="https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400"),
    Product(shop_id=shop2.id, title="Smart Watch Series 5", description="Fitness tracker with heart rate monitor and GPS.", price=8500, stock=15, category="wearables", attributes='{"color":"black"}', image_url="https://images.unsplash.com/photo-1523275148826-6af2f2c8d1d0?w=400"),
    Product(shop_id=shop2.id, title="Bluetooth Speaker", description="Portable speaker with deep bass. 12h battery life.", price=3500, stock=20, category="audio", attributes='{"color":"blue"}', image_url="https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400"),
    Product(shop_id=shop2.id, title="64GB USB Flash Drive", description="High-speed USB 3.0 flash drive. Plug and play.", price=1500, stock=50, category="storage", image_url="https://images.unsplash.com/photo-1618410320928-25228d811631?w=400"),

    # Style Hub Fashion - Fashion
    Product(shop_id=shop3.id, title="Classic White Sneakers", description="Timeless white sneakers, comfortable and durable.", price=4500, stock=20, category="shoes", attributes='{"color":"white","size":"42"}', image_url="https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400"),
    Product(shop_id=shop3.id, title="Leather Ankle Boots", description="Stylish brown leather boots for men and women.", price=6500, stock=15, category="shoes", attributes='{"color":"brown","size":"43"}', image_url="https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400"),
    Product(shop_id=shop3.id, title="Running Shoes", description="Breathable mesh running shoes with cushioned sole.", price=5500, stock=18, category="shoes", attributes='{"color":"blue","size":"44"}', image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"),
    Product(shop_id=shop3.id, title="Cotton T-Shirt Pack", description="Pack of 3 premium cotton t-shirts in different colors.", price=2500, stock=30, category="clothing", attributes='{"size":"L"}', image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400"),
    Product(shop_id=shop3.id, title="Denim Jeans", description="Classic fit denim jeans, comfortable and stylish.", price=3800, stock=25, category="clothing", attributes='{"size":"32","color":"blue"}', image_url="https://images.unsplash.com/photo-1542272604-787c3835535d?w=400"),

    # Home Comforts Kenya - Home & Furniture
    Product(shop_id=shop4.id, title="Coffee Table", description="Modern wooden coffee table for living room.", price=12000, stock=10, category="furniture", image_url="https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400"),
    Product(shop_id=shop4.id, title="Floor Lamp", description="Elegant floor lamp with adjustable brightness.", price=4500, stock=15, category="lighting", image_url="https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400"),
    Product(shop_id=shop4.id, title="Throw Pillows Set", description="Set of 4 decorative throw pillows.", price=2500, stock=20, category="decor", image_url="https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=400"),
    Product(shop_id=shop4.id, title="Wall Art Canvas", description="Modern abstract wall art on canvas.", price=3500, stock=12, category="decor", image_url="https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=400"),
    Product(shop_id=shop4.id, title="Bed Sheet Set", description="Premium cotton bed sheet set (queen size).", price=4000, stock=18, category="bedding", image_url="https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=400"),

    # Glow Beauty Store - Beauty & Cosmetics
    Product(shop_id=shop5.id, title="Face Moisturizer", description="Hydrating face moisturizer for all skin types.", price=1800, stock=35, category="skincare", image_url="https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?w=400"),
    Product(shop_id=shop5.id, title="Lipstick Set", description="Set of 3 long-lasting matte lipsticks.", price=2200, stock=25, category="makeup", attributes='{"shade":"red,pink, nude"}', image_url="https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400"),
    Product(shop_id=shop5.id, title="Hair Serum", description="Nourishing hair serum for smooth, shiny hair.", price=1500, stock=30, category="haircare", image_url="https://images.unsplash.com/photo-1526947425960-945c6e72858f?w=400"),
    Product(shop_id=shop5.id, title="Foundation", description="Full coverage foundation, multiple shades available.", price=2800, stock=20, category="makeup", attributes='{"shade":"medium"}', image_url="https://images.unsplash.com/photo-1631214524020-7e18db9a8f92?w=400"),
    Product(shop_id=shop5.id, title="Body Lotion", description="Moisturizing body lotion with natural ingredients.", price=1200, stock=40, category="skincare", image_url="https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?w=400"),

    # FitLife Sports Kenya - Sports & Fitness
    Product(shop_id=shop6.id, title="Yoga Mat", description="Non-slip yoga mat, 6mm thick.", price=1800, stock=25, category="fitness", image_url="https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400"),
    Product(shop_id=shop6.id, title="Dumbbells Set", description="Set of adjustable dumbbells (5-20kg).", price=8500, stock=10, category="fitness", image_url="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400"),
    Product(shop_id=shop6.id, title="Running Shorts", description="Lightweight running shorts with pockets.", price=1500, stock=30, category="clothing", attributes='{"size":"M"}', image_url="https://images.unsplash.com/photo-1596079890701-dd42edf5b4ac?w=400"),
    Product(shop_id=shop6.id, title="Sports Water Bottle", description="Insulated water bottle, 1L capacity.", price=1200, stock=35, category="accessories", image_url="https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400"),
    Product(shop_id=shop6.id, title="Resistance Bands Set", description="Set of 5 resistance bands for strength training.", price=1500, stock=28, category="fitness", image_url="https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=400"),

    # Bookworm Kenya - Books & Stationery
    Product(shop_id=shop7.id, title="Notebook A5", description="Premium ruled notebook, 200 pages.", price=300, stock=50, category="stationery", image_url="https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=400"),
    Product(shop_id=shop7.id, title="Ballpoint Pens Set", description="Set of 10 black ballpoint pens.", price=400, stock=40, category="stationery", image_url="https://images.unsplash.com/photo-1585336261022-680e295ce3fe?w=400"),
    Product(shop_id=shop7.id, title="Bestseller Novel", description="Popular fiction novel, latest release.", price=1200, stock=20, category="books", image_url="https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400"),
    Product(shop_id=shop7.id, title="Backpack", description="Durable backpack with laptop compartment.", price=3500, stock=15, category="accessories", image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"),
    Product(shop_id=shop7.id, title="Desk Organizer", description="Wooden desk organizer for office supplies.", price=1500, stock=25, category="stationery", image_url="https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400"),

    # AutoParts Kenya - Automotive
    Product(shop_id=shop8.id, title="Car Floor Mats", description="Universal fit car floor mats, set of 4.", price=2500, stock=20, category="accessories", image_url="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"),
    Product(shop_id=shop8.id, title="LED Headlight Bulbs", description="Bright LED headlight bulbs, H4 type.", price=3500, stock=15, category="lighting", image_url="https://images.unsplash.com/photo-1591293836027-e05b48473b67?w=400"),
    Product(shop_id=shop8.id, title="Car Phone Mount", description="Universal phone mount for dashboard.", price=800, stock=35, category="accessories", image_url="https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=400"),
    Product(shop_id=shop8.id, title="Car Cover", description="Waterproof car cover, universal size.", price=4500, stock=12, category="accessories", image_url="https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400"),
    Product(shop_id=shop8.id, title="Engine Oil 5W-30", description="Synthetic engine oil, 5L can.", price=5500, stock=18, category="maintenance", image_url="https://images.unsplash.com/photo-1635784063466-7783e924e9f4?w=400"),

    # Wellness Hub Kenya - Health & Wellness
    Product(shop_id=shop9.id, title="Multivitamins", description="Daily multivitamin supplement, 60 tablets.", price=1800, stock=30, category="supplements", image_url="https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400"),
    Product(shop_id=shop9.id, title="Protein Powder", description="Whey protein powder, 2kg chocolate flavor.", price=5500, stock=20, category="supplements", image_url="https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=400"),
    Product(shop_id=shop9.id, title="Essential Oils Set", description="Set of 5 pure essential oils.", price=2200, stock=25, category="wellness", image_url="https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=400"),
    Product(shop_id=shop9.id, title="Honey (500g)", description="Pure natural honey from local beekeepers.", price=800, stock=40, category="food", image_url="https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400"),
    Product(shop_id=shop9.id, title="Herbal Tea Pack", description="Assorted herbal tea pack, 20 bags.", price=600, stock=35, category="beverages", image_url="https://images.unsplash.com/photo-1597318181409-cf64d0b5d8a2?w=400"),

    # Pet Paradise Kenya - Pets & Pet Supplies
    Product(shop_id=shop10.id, title="Dog Food Premium", description="Premium dog food, 10kg bag.", price=3500, stock=20, category="pet_food", image_url="https://images.unsplash.com/photo-1589924691195-41432c84c161?w=400"),
    Product(shop_id=shop10.id, title="Cat Food Premium", description="Premium cat food, 5kg bag.", price=2800, stock=25, category="pet_food", image_url="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400"),
    Product(shop_id=shop10.id, title="Pet Leash", description="Durable pet leash for dogs, adjustable length.", price=800, stock=30, category="accessories", image_url="https://images.unsplash.com/photo-1601758125946-6ec2ef64daf8?w=400"),
    Product(shop_id=shop10.id, title="Pet Bed Medium", description="Comfortable pet bed, medium size.", price=2200, stock=15, category="accessories", image_url="https://images.unsplash.com/photo-1541599468348-e96984315921?w=400"),
    Product(shop_id=shop10.id, title="Pet Toys Set", description="Assorted pet toys for cats and dogs.", price=1200, stock=28, category="toys", image_url="https://images.unsplash.com/photo-1535294435445-d7249524ef2e?w=400"),
]

db.add_all(prods)
db.commit()

db.close()

print("Database seeded successfully!")
print(f"  - {14} users (1 admin, 10 sellers, 3 buyers)")
print(f"  - {10} shops created across different categories:")
print(f"    1. Fresh Market Kenya (food)")
print(f"    2. Tech Galaxy Kenya (electronics)")
print(f"    3. Style Hub Fashion (fashion)")
print(f"    4. Home Comforts Kenya (home)")
print(f"    5. Glow Beauty Store (beauty)")
print(f"    6. FitLife Sports Kenya (sports)")
print(f"    7. Bookworm Kenya (books)")
print(f"    8. AutoParts Kenya (automotive)")
print(f"    9. Wellness Hub Kenya (health)")
print(f"    10. Pet Paradise Kenya (pets)")
print(f"  - {len(prods)} products created")
print()
print("Test accounts:")
print("  admin / admin123  (full access)")
print("  john  / seller123 (owns Fresh Market Kenya)")
print("  mary  / seller123 (owns Tech Galaxy Kenya)")
print("  peter / seller123 (owns Style Hub Fashion)")
print("  grace / seller123 (owns Home Comforts Kenya)")
print("  david / seller123 (owns Glow Beauty Store)")
print("  susan / seller123 (owns FitLife Sports Kenya)")
print("  james / seller123 (owns Bookworm Kenya)")
print("  hannah/ seller123 (owns AutoParts Kenya)")
print("  robert/ seller123 (owns Wellness Hub Kenya)")
print("  esther/ seller123 (owns Pet Paradise Kenya)")
print("  alice / buyer123  (buyer)")
print("  bob   / buyer123  (buyer)")
print("  charles/ buyer123  (buyer)")
