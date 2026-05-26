from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from core.database import get_db
from dependencies.auth import get_current_user
from models import User, IkobizListing, IkobizListingStatus

router = APIRouter(tags=["ikobiz"])


class IkobizListingCreate(BaseModel):
    seller_name: str
    title: str
    description: str | None = None
    starting_price: float
    buy_now_price: float | None = None
    quantity: int = 1
    image_url: str | None = None


class IkobizListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    starting_price: float | None = None
    buy_now_price: float | None = None
    quantity: int | None = None
    image_url: str | None = None
    status: str | None = None


@router.get("/ikobiz/products")
def get_all_ikobiz_listings(
    seller_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    has_buy_now: Optional[bool] = Query(None),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(IkobizListing)

    if seller_id:
        q = q.filter(IkobizListing.seller_id == seller_id)
    if status:
        q = q.filter(IkobizListing.status == status)
    if search:
        q = q.filter(IkobizListing.title.ilike(f"%{search}%"))
    if min_price is not None:
        q = q.filter(IkobizListing.starting_price >= min_price)
    if max_price is not None:
        q = q.filter(IkobizListing.starting_price <= max_price)
    if has_buy_now is True:
        q = q.filter(IkobizListing.buy_now_price.isnot(None))
    elif has_buy_now is False:
        q = q.filter(IkobizListing.buy_now_price.is_(None))

    if sort == "price_asc":
        q = q.order_by(IkobizListing.starting_price.asc())
    elif sort == "price_desc":
        q = q.order_by(IkobizListing.starting_price.desc())
    elif sort == "oldest":
        q = q.order_by(IkobizListing.created_at.asc())
    else:
        q = q.order_by(IkobizListing.created_at.desc())

    products = q.all()
    result = []
    for p in products:
        result.append({
            "id": p.id,
            "seller_id": p.seller_id,
            "seller_name": p.seller_name,
            "title": p.title,
            "description": p.description,
            "starting_price": p.starting_price,
            "buy_now_price": p.buy_now_price,
            "quantity": p.quantity,
            "image_url": p.image_url,
            "status": p.status.value if p.status else "OPEN",
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return result


@router.post("/ikobiz/products", status_code=201)
def create_ikobiz_listing(
    data: IkobizListingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.starting_price <= 0:
        raise HTTPException(status_code=400, detail="Starting price must be greater than 0")
    if data.buy_now_price is not None and data.buy_now_price < data.starting_price:
        raise HTTPException(status_code=400, detail="Buy-now price must be at least the starting price")

    product = IkobizListing(
        seller_id=user.id,
        seller_name=data.seller_name,
        title=data.title,
        description=data.description,
        starting_price=data.starting_price,
        buy_now_price=data.buy_now_price,
        quantity=data.quantity,
        image_url=data.image_url,
        status=IkobizListingStatus.OPEN,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return {
        "id": product.id,
        "seller_id": product.seller_id,
        "seller_name": product.seller_name,
        "title": product.title,
        "description": product.description,
        "starting_price": product.starting_price,
        "buy_now_price": product.buy_now_price,
        "quantity": product.quantity,
        "image_url": product.image_url,
        "status": product.status.value if product.status else "OPEN",
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


@router.get("/ikobiz/products/{product_id}")
def get_single_ikobiz_listing(product_id: int, db: Session = Depends(get_db)):
    product = db.query(IkobizListing).filter(IkobizListing.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ikobiz listing not found")
    return {
        "id": product.id,
        "seller_id": product.seller_id,
        "seller_name": product.seller_name,
        "title": product.title,
        "description": product.description,
        "starting_price": product.starting_price,
        "buy_now_price": product.buy_now_price,
        "quantity": product.quantity,
        "image_url": product.image_url,
        "status": product.status.value if product.status else "OPEN",
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


@router.put("/ikobiz/products/{product_id}")
def update_ikobiz_listing(
    product_id: int,
    data: IkobizListingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = db.query(IkobizListing).filter(IkobizListing.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ikobiz listing not found")
    if product.seller_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not own this listing")

    if data.title is not None:
        product.title = data.title
    if data.description is not None:
        product.description = data.description
    if data.starting_price is not None:
        product.starting_price = data.starting_price
    if data.buy_now_price is not None:
        product.buy_now_price = data.buy_now_price
    if data.quantity is not None:
        product.quantity = data.quantity
    if data.image_url is not None:
        product.image_url = data.image_url
    if data.status is not None:
        product.status = IkobizListingStatus(data.status)

    db.commit()
    db.refresh(product)
    return {"message": "Listing updated"}


@router.delete("/ikobiz/products/{product_id}", status_code=204)
def delete_ikobiz_listing(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = db.query(IkobizListing).filter(IkobizListing.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ikobiz listing not found")
    if product.seller_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not own this listing")
    db.delete(product)
    db.commit()
    return None


@router.get("/seller/ikobiz-listings")
def get_seller_ikobiz_listings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    products = db.query(IkobizListing).filter(IkobizListing.seller_id == user.id).order_by(IkobizListing.created_at.desc()).all()
    result = []
    for p in products:
        result.append({
            "id": p.id,
            "title": p.title,
            "starting_price": p.starting_price,
            "buy_now_price": p.buy_now_price,
            "quantity": p.quantity,
            "image_url": p.image_url,
            "status": p.status.value if p.status else "OPEN",
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "offer_count": len(p.negotiations) if p.negotiations else 0,
        })
    return result
