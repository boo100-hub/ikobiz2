"""
seed_rajo.py - Idempotent seed for test seller "rajo" with shop "rajo's electronics".

Run: python seed_rajo.py
"""

from core.database import SessionLocal
from core.security import hash_password
from models import User, Shop, Product

db = SessionLocal()

# Upsert seller user
rajo = db.query(User).filter(User.email == "rajo@ikobiz.com").first()
if rajo:
    rajo.username = "rajo"
    rajo.phone = "254714114994"
    rajo.password_hash = hash_password("seller123")
    rajo.role = "seller"
    print("  ↻ Updated existing user 'rajo'")
else:
    rajo = User(
        username="rajo",
        email="rajo@ikobiz.com",
        phone="254714114994",
        password_hash=hash_password("seller123"),
        role="seller",
    )
    db.add(rajo)
    print("  ✓ Created user 'rajo'")
db.flush()

# Upsert shop
shop = db.query(Shop).filter(Shop.slug == "rajos-electronics").first()
if shop:
    shop.owner_id = rajo.id
    shop.name = "rajo's electronics"
    shop.description = "Premium phones, laptops, and electronics at the best prices in town."
    shop.banner_image = "https://images.unsplash.com/photo-1468495244123-6c6c332eeece?w=800"
    print("  ↻ Updated existing shop 'rajo's electronics'")
else:
    shop = Shop(
        owner_id=rajo.id,
        name="rajo's electronics",
        slug="rajos-electronics",
        description="Premium phones, laptops, and electronics at the best prices in town.",
        banner_image="https://images.unsplash.com/photo-1468495244123-6c6c332eeece?w=800",
    )
    db.add(shop)
    print("  ✓ Created shop 'rajo's electronics'")
db.flush()

# Set up products (skip existing ones by title)
products_data = [
    ("iPhone 15 Pro Max - 256GB", "Latest iPhone with A17 Pro chip, titanium design, and 48MP camera system. Brand new with 1-year warranty.", 189000.00, 10, "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400"),
    ("Samsung Galaxy S24 Ultra - 512GB", "Premium Android flagship with S Pen, 200MP camera, and Galaxy AI features.", 165000.00, 8, "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400"),
    ("MacBook Pro 14\" M3 Pro - 18GB RAM", "Apple MacBook Pro with M3 Pro chip, 18GB unified memory, 512GB SSD. Perfect for professionals.", 295000.00, 5, "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400"),
    ("HP Spectre x360 - 16GB RAM", "Premium 2-in-1 laptop with Intel Core i7, 16GB RAM, 512GB SSD, and 4K OLED touchscreen.", 145000.00, 7, "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400"),
    ("Tecno Camon 20 Pro", "Affordable mid-range smartphone with 64MP camera, 8GB RAM, and 5000mAh battery.", 35000.00, 25, "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=400"),
    ("Dell XPS 15 - Intel i9", "High-performance laptop with Intel Core i9, 32GB RAM, 1TB SSD, and NVIDIA RTX 4060.", 250000.00, 3, "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400"),
]

existing_titles = {p.title for p in db.query(Product).filter(Product.shop_id == shop.id).all()}
added = 0
for title, desc, price, stock, img in products_data:
    if title not in existing_titles:
        db.add(Product(shop_id=shop.id, title=title, description=desc, price=price, stock=stock, image_url=img))
        added += 1

db.commit()
db.close()

print(f"  ✓ {added} new product(s) added")
print(f"  - Total products: {len(products_data)}")
print()
print("Test seller ready!")
print(f"  Phone: +254714114994")
print(f"  Login: rajo / seller123")
print(f"  Shop: rajo's electronics")
