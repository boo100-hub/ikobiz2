"""
seed_demo.py - Add demo seed data for pitch presentation.

Does NOT remove existing data. Only inserts records that don't already exist.
Run: python seed_demo.py
"""

from core.database import SessionLocal
from core.security import hash_password
from models import User, PickupPoint, Shop, Product, ProductStatus

BUYER_PHONE = "254714114994"


def get_or_none(model, **kwargs):
    db = SessionLocal()
    try:
        return db.query(model).filter_by(**kwargs).first()
    finally:
        db.close()


def seed_demo_data():
    db = SessionLocal()

    try:
        # =================================================================
        # Resolve phone conflict: "john" (seller) has the buyer's phone.
        # Move john to a different number so demo_buyer can use it.
        # =================================================================
        john = db.query(User).filter(User.username == "john").first()
        if john and john.phone == BUYER_PHONE:
            john.phone = "254714114995"
            print("  ↳ Updated john's phone to 254714114995 (freed 254714114994 for buyer)")
            db.flush()

        # =================================================================
        # USERS (skip if username already exists)
        # =================================================================

        users_data = [
            dict(username="admin", email="admin@ikobiz.com", phone="254700000000",
                 password_hash=hash_password("admin123"), role="admin"),
            dict(username="mama_mboga", email="mama@ikobiz.com", phone="254702193430",
                 password_hash=hash_password("seller123"), role="seller"),
            dict(username="techhub", email="techhub@ikobiz.com", phone="254700000011",
                 password_hash=hash_password("seller123"), role="seller"),
            dict(username="demo_buyer", email="demo@ikobiz.com", phone=BUYER_PHONE,
                 password_hash=hash_password("buyer123"), role="buyer"),
        ]

        created_users = []
        for ud in users_data:
            existing = db.query(User).filter(User.username == ud["username"]).first()
            if existing:
                print(f"  ✓ User '{ud['username']}' already exists (id={existing.id})")
                created_users.append(existing)
            else:
                user = User(**ud)
                db.add(user)
                db.flush()
                print(f"  + Created user '{ud['username']}' (id={user.id})")
                created_users.append(user)

        admin = created_users[0]
        seller_mama = created_users[1]
        seller_techhub = created_users[2]
        demo_buyer = created_users[3]

        # =================================================================
        # PICKUP POINTS (skip if name already exists)
        # =================================================================

        pickup_data = [
            # Nairobi hyperlocal pickup points
            dict(name="Westlands Mall Pickup Point", area="Westlands", lat=-1.2676, lng=36.8108),
            dict(name="CBD - Kencom Bus Stop", area="Nairobi CBD", lat=-1.2833, lng=36.8219),
            dict(name="Kilimani - Yaya Centre", area="Kilimani", lat=-1.2858, lng=36.8005),
            dict(name="Kasarani - Mwiki Stage", area="Kasarani", lat=-1.2222, lng=36.8950),
            dict(name="Eastlands - Buruburu", area="Buruburu", lat=-1.2919, lng=36.8747),
            # Nyeri (existing)
            dict(name="DeKUT Main Gate", area="Nyeri", lat=-0.4212, lng=36.9493),
            dict(name="Nyeri Town Stage", area="Nyeri Town", lat=-0.4200, lng=36.9470),
            dict(name="Dedan Kimathi Stage", area="Nyeri", lat=-0.4195, lng=36.9500),
        ]

        for pd in pickup_data:
            existing = db.query(PickupPoint).filter(PickupPoint.name == pd["name"]).first()
            if existing:
                print(f"  ✓ Pickup point '{pd['name']}' already exists (id={existing.id})")
            else:
                pp = PickupPoint(**pd)
                db.add(pp)
                db.flush()
                print(f"  + Created pickup point '{pd['name']}' (id={pp.id})")

        db.commit()

        # =================================================================
        # TECHHUB SHOP (pre-seeded, skip if slug exists)
        # =================================================================

        techhub_shop = db.query(Shop).filter(Shop.slug == "techhub-electronics").first()
        if techhub_shop:
            print(f"  ✓ Shop 'TechHub Electronics' already exists (id={techhub_shop.id})")
        else:
            techhub_shop = Shop(
                owner_id=seller_techhub.id,
                name="TechHub Electronics",
                slug="techhub-electronics",
                description="Quality electronics and phone accessories at affordable prices in Westlands.",
                banner_image="https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800",
                category="electronics",
                location_area="Westlands",
                location_gps_lat=-1.2676,
                location_gps_lng=36.8108,
                pickup_address="Westlands Mall, 1st Floor, Shop 7, Nairobi",
                fulfillment_modes="pickup,seller_delivery",
                delivery_radius_km=10.0,
                delivery_fee=200,
                payment_methods="mpesa,cash_on_delivery",
                operating_hours='{"mon-fri":"09:00-20:00","sat":"09:00-18:00","sun":"closed"}',
                phone="254700000011",
            )
            db.add(techhub_shop)
            db.flush()
            print(f"  + Created shop 'TechHub Electronics' (id={techhub_shop.id})")

        # =================================================================
        # TECHHUB PRODUCTS (skip if title + shop_id already exist)
        # =================================================================

        techhub_products_data = [
            dict(title="Phone Charger",
                 description="Universal micro-USB phone charger, 2A fast charging.",
                 price=500, stock=30,
                 image_url="https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400"),
            dict(title="USB Cable",
                 description="1m braided USB-A to micro-USB cable, durable.",
                 price=300, stock=40,
                 image_url="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"),
            dict(title="Earphones",
                 description="In-ear stereo earphones with microphone, compatible with smartphones.",
                 price=800, stock=25,
                 image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e"),
            dict(title="Power Bank",
                 description="10,000mAh portable power bank with dual USB output.",
                 price=1500, stock=20,
                 image_url="https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5"),
        ]

        for pd in techhub_products_data:
            existing = db.query(Product).filter(
                Product.shop_id == techhub_shop.id,
                Product.title == pd["title"],
            ).first()
            if existing:
                print(f"  ✓ Product '{pd['title']}' already exists (id={existing.id})")
            else:
                product = Product(
                    shop_id=techhub_shop.id,
                    title=pd["title"],
                    description=pd["description"],
                    price=pd["price"],
                    stock=pd["stock"],
                    status=ProductStatus.ACTIVE,
                    image_url=pd["image_url"],
                )
                db.add(product)
                db.flush()
                print(f"  + Created product '{pd['title']}' (id={product.id})")

        # =================================================================
        # FRESH MARKET KENYA (mama_mboga's shop with fresh produce)
        # =================================================================

        mama_shop = db.query(Shop).filter(Shop.slug == "fresh-market-kenya").first()
        if mama_shop:
            print(f"  ✓ Shop 'Fresh Market Kenya' already exists (id={mama_shop.id})")
        else:
            mama_shop = Shop(
                owner_id=seller_mama.id,
                name="Fresh Market Kenya",
                slug="fresh-market-kenya",
                description="Farm-fresh produce delivered across Nairobi. Kales, tomatoes, onions, and more!",
                banner_image="https://images.unsplash.com/photo-1542838132-92c53300491e?w=800",
                category="groceries",
                location_area="Westlands",
                location_gps_lat=-1.2676,
                location_gps_lng=36.8108,
                pickup_address="Westlands Mall, Ground Floor, Fresh Produce Section",
                fulfillment_modes="pickup",
                delivery_radius_km=0,
                delivery_fee=0,
                payment_methods="mpesa",
                operating_hours='{"mon-sat":"06:00-20:00","sun":"08:00-18:00"}',
                phone="254702193430",
            )
            db.add(mama_shop)
            db.flush()
            print(f"  + Created shop 'Fresh Market Kenya' (id={mama_shop.id})")

        mama_products_data = [
            dict(title="Fresh Kale (1 bunch)",
                 description="Locally grown sukuma wiki, fresh from the farm.",
                 price=80, stock=100, category="vegetables",
                 image_url="https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400"),
            dict(title="Organic Tomatoes (1kg)",
                 description="Juicy, vine-ripened organic tomatoes straight from Kiambu.",
                 price=150, stock=80, category="vegetables",
                 image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400"),
            dict(title="Red Onions (1kg)",
                 description="Sweet red onions, perfect for cooking and salads.",
                 price=120, stock=60, category="vegetables",
                 image_url="https://images.unsplash.com/photo-1508747703725-719d64ab7a64?w=400"),
            dict(title="Irish Potatoes (1kg)",
                 description="High-quality potatoes from the central highlands.",
                 price=130, stock=90, category="vegetables",
                 image_url="https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=400"),
            dict(title="Fresh Avocados (each)",
                 description="Ripe, creamy avocados perfect for salads and toast.",
                 price=60, stock=50, category="fruits",
                 image_url="https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=400"),
            dict(title="Mangoes (each)",
                 description="Sweet, juicy mangoes — a Kenyan favorite!",
                 price=50, stock=100, category="fruits",
                 image_url="https://images.unsplash.com/photo-1553279768-865429fa0078?w=400"),
        ]

        for pd in mama_products_data:
            existing = db.query(Product).filter(
                Product.shop_id == mama_shop.id,
                Product.title == pd["title"],
            ).first()
            if existing:
                print(f"  ✓ Product '{pd['title']}' already exists (id={existing.id})")
            else:
                product = Product(
                    shop_id=mama_shop.id,
                    title=pd["title"],
                    description=pd["description"],
                    price=pd["price"],
                    stock=pd["stock"],
                    status=ProductStatus.ACTIVE,
                    category=pd["category"],
                    image_url=pd["image_url"],
                )
                db.add(product)
                db.flush()
                print(f"  + Created product '{pd['title']}' (id={product.id})")

        db.commit()

        print()
        print("====================================")
        print("Demo seed data added successfully")
        print("====================================")
        print("Users: 4 (admin, mama_mboga, techhub, demo_buyer)")
        print("Pickup Points: 8 (5 Nairobi + 3 Nyeri)")
        print("Shops: TechHub Electronics (4 products), Fresh Market Kenya (6 products)")
        print()
        print("📱 WhatsApp demo buyer phone: 254714114994 (demo_buyer)")
        print("📱 Mama Mboga phone: 254702193430 (seller, Fresh Market Kenya)")
        print("📱 TechHub phone: 254700000011 (seller, TechHub Electronics)")
        print()
        print("Flow: Buyer texts WhatsApp -> discovers shops -> picks pickup point")
        print("     -> sees checkout -> confirms -> seller gets notified")

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
