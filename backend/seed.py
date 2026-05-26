"""
seed.py - Populates the database with sample data for all markets.

Run: python seed.py
"""

from core.database import SessionLocal
from core.security import hash_password
from models import User, Shop, Product, ProductStatus, IkobizListing, IkobizListingStatus, Negotiation, Order, OrderStatus

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

shop1 = Shop(owner_id=alice.id, name="Mama Mboga", slug="mama-mboga",
             description="Fresh farm produce delivered daily. Fruits, vegetables, and organic goods straight from the farm.",
             banner_image="https://images.unsplash.com/photo-1610348725531-843dff563e2c?w=800")

shop2 = Shop(owner_id=bob.id, name="Tech Store", slug="tech-store",
             description="Gadgets, accessories, and electronics at affordable prices. From phone cases to laptops.",
             banner_image="https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800")

shop3 = Shop(owner_id=diana.id, name="Shoe Palace", slug="shoe-palace",
             description="Sneakers, boots, sandals, and more. Trendy footwear for every occasion.",
             banner_image="https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=800")

db.add_all([shop1, shop2, shop3])
db.commit()

# =====================================================================
# PRIMARY MARKET — products
# =====================================================================

prods = [
    Product(shop_id=shop1.id, title="Organic Tomatoes (1kg)", description="Ripe, juicy tomatoes straight from the farm.", price=2.50, stock=50, image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400"),
    Product(shop_id=shop1.id, title="Fresh Kale (1 bunch)", description="Crisp green kale, perfect for sukuma wiki.", price=1.20, stock=80, image_url="https://images.unsplash.com/photo-1524179091875-bf99a9a6af89?w=400"),
    Product(shop_id=shop1.id, title="Ripe Bananas (1 bunch)", description="Sweet yellow bananas, great for snacking.", price=1.80, stock=60, image_url="https://images.unsplash.com/photo-1603833665858-e61d17a6f42f?w=400"),
    Product(shop_id=shop2.id, title="Wireless Bluetooth Earbuds", description="Compact earbuds with noise cancellation and 8h battery.", price=25.00, stock=30, image_url="https://images.unsplash.com/photo-1590658268037-6bf12f032f55?w=400"),
    Product(shop_id=shop2.id, title="USB-C Hub 7-in-1", description="Multi-port adapter with HDMI, USB 3.0, SD card reader.", price=18.00, stock=40, image_url="https://images.unsplash.com/photo-1623869675781-80aa31012a5a?w=400"),
    Product(shop_id=shop2.id, title="Phone Stand Adjustable", description="Aluminum adjustable stand for desk or bedside.", price=12.00, stock=25, image_url="https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400"),
    Product(shop_id=shop3.id, title="Classic White Sneakers", description="Timeless white sneakers, comfortable and durable.", price=45.00, stock=20, image_url="https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400"),
    Product(shop_id=shop3.id, title="Leather Ankle Boots", description="Stylish brown leather boots for men and women.", price=65.00, stock=15, image_url="https://images.unsplash.com/photo-1638247025967-b4e38f787b76?w=400"),
    Product(shop_id=shop3.id, title="Slip-on Sandals", description="Lightweight summer sandals with cushioned sole.", price=22.00, stock=35, image_url="https://images.unsplash.com/photo-1603481588273-2f908a9a7a1b?w=400"),
]
db.add_all(prods)
db.commit()

# =====================================================================
# IKOBIZ — negotiation/bidding listings
# =====================================================================

ik1 = IkobizListing(seller_id=eve.id, seller_name="Eve", title="HP Laptop - Core i5, 8GB RAM",
                    description="Used HP laptop in good condition. Comes with charger. 256GB SSD.",
                    starting_price=50000, buy_now_price=58000, quantity=1,
                    image_url="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400",
                    status=IkobizListingStatus.NEGOTIATING)

ik2 = IkobizListing(seller_id=eve.id, seller_name="Eve", title="Sony PlayStation 4 - 1TB",
                    description="PS4 slim, barely used. Includes 2 controllers and 5 games.",
                    starting_price=35000, buy_now_price=40000, quantity=1,
                    image_url="https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=400",
                    status=IkobizListingStatus.OPEN)

ik3 = IkobizListing(seller_id=frank.id, seller_name="Frank", title="Wooden Dining Table - 6 Seater",
                    description="Solid mahogany dining table. Slight scratch on one leg but very sturdy.",
                    starting_price=25000, buy_now_price=None, quantity=1,
                    image_url="https://images.unsplash.com/photo-1530018607912-eff2daa1bac4?w=400",
                    status=IkobizListingStatus.OPEN)

ik4 = IkobizListing(seller_id=eve.id, seller_name="Eve", title="Samsung Galaxy S22 - 128GB",
                    description="Like new, barely used. Comes with original box and charger.",
                    starting_price=45000, buy_now_price=52000, quantity=1,
                    image_url="https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400",
                    status=IkobizListingStatus.OPEN)

ik5 = IkobizListing(seller_id=frank.id, seller_name="Frank", title="Electric Kettle - 1.7L",
                    description="Brand new, never used. Stainless steel body with auto shut-off.",
                    starting_price=1500, buy_now_price=2000, quantity=5,
                    image_url="https://images.unsplash.com/photo-1594226801341-41427b4e5c22?w=400",
                    status=IkobizListingStatus.OPEN)

db.add_all([ik1, ik2, ik3, ik4, ik5])
db.commit()

# Sample negotiation thread
n1 = Negotiation(ikobiz_listing_id=ik1.id, buyer_name="Bob", offer_price=42000,
                 message="Hi Eve, I'm interested in the laptop. Would you take 42,000?", is_counter_offer=0)
db.add(n1)
db.commit()

n2 = Negotiation(ikobiz_listing_id=ik1.id, buyer_name="Eve", offer_price=47000,
                 message="I can do 47,000. It's in great condition.", is_counter_offer=1)
db.add(n2)
db.commit()

n3 = Negotiation(ikobiz_listing_id=ik1.id, buyer_name="Bob", offer_price=45000,
                 message="Alright, let's meet at 45,000 and we have a deal.", is_counter_offer=0)
db.add(n3)
db.commit()

db.close()

print("Database seeded successfully!")
print(f"  - {6} users (admin, 3 sellers, 2 buyers)")
print(f"  - {3} shops created")
print(f"  - {len(prods)} primary products created")
print(f"  - {5} ikobiz listings created")
print(f"  - {3} negotiation offers created")
print()
print("Test accounts:")
print("  admin / admin123  (full access)")
print("  alice / seller123 (owns Mama Mboga)")
print("  bob   / seller123 (owns Tech Store)")
print("  diana / seller123 (owns Shoe Palace)")
print("  eve   / buyer123  (individual seller / buyer)")
print("  frank / buyer123  (buyer)")
