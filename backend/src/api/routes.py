from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import List, Optional
from asyncpg import Connection
from datetime import datetime

from . import models
from .db import get_db
from .utils import hash_password, verify_password, create_access_token, verify_access_token

router = APIRouter()

# ---------------------------------------------------------------------------
# Dependency to get current user from simple header (replace with OAuth/JWT)
async def get_current_user(authorization: Optional[str] = Header(None), db: Connection = Depends(get_db)) -> models.User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    user = await db.fetchrow("SELECT id, username, email FROM users WHERE id=$1", user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return models.User(**dict(user))


# ---------------------------------------------------------------------------
# PUBLIC_INTERFACE
@router.post("/auth/register", response_model=models.User, summary="User Registration", tags=["Auth"])
async def register(user: models.UserCreate, db: Connection = Depends(get_db)):
    """
    Register a new user.
    """
    existing = await db.fetchrow("SELECT id FROM users WHERE email=$1", user.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    password_hash = hash_password(user.password)
    record = await db.fetchrow(
        "INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3) RETURNING id, username, email",
        user.username, user.email, password_hash)
    return models.User(**dict(record))

# PUBLIC_INTERFACE
@router.post("/auth/login", response_model=dict, summary="User Login", tags=["Auth"])
async def login(credentials: models.UserLogin, db: Connection = Depends(get_db)):
    """
    Authenticate a user and return an access token.
    """
    user = await db.fetchrow("SELECT id, username, email, password_hash FROM users WHERE email=$1", credentials.email)
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer"}

# ---------------------------------------------------------------------------
# PUBLIC_INTERFACE
@router.get("/cakes/", response_model=List[models.Cake], summary="Cake Catalog", tags=["Cake"])
async def list_cakes(db: Connection = Depends(get_db)):
    """
    Browse the cake catalog.
    """
    cakes = await db.fetch("SELECT * FROM cakes")
    result = []
    for cake in cakes:
        result.append(models.Cake(
            id=cake["id"],
            name=cake["name"],
            description=cake["description"],
            base_price=cake["base_price"],
            image_url=cake["image_url"],
            available_sizes=cake["available_sizes"],
            available_flavors=cake["available_flavors"],
            available_toppings=cake["available_toppings"]
        ))
    return result

# PUBLIC_INTERFACE
@router.get("/cakes/{cake_id}", response_model=models.Cake, summary="Get Cake detail", tags=["Cake"])
async def get_cake(cake_id: int, db: Connection = Depends(get_db)):
    """
    Get detailed info of a cake.
    """
    cake = await db.fetchrow("SELECT * FROM cakes WHERE id=$1", cake_id)
    if not cake:
        raise HTTPException(status_code=404, detail="Cake not found")
    return models.Cake(**dict(cake))

# ---------------------------------------------------------------------------
# PUBLIC_INTERFACE
@router.post("/orders/", response_model=models.Order, summary="Place an order", tags=["Order"])
async def place_order(order: models.OrderCreate,
                     db: Connection = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    """
    Place an order for a cake (with customization).
    """
    now = datetime.utcnow()
    # Calculate total price: price = cake.base_price + toppings + etc.
    cake = await db.fetchrow("SELECT * FROM cakes WHERE id=$1", order.cake_id)
    if not cake:
        raise HTTPException(status_code=404, detail="Cake not found")
    total_price = float(cake["base_price"]) + len(order.customization.toppings) * 2.0  # Simple price logic
    
    # Store customization as JSON string for simplicity
    customization_dict = order.customization.dict()
    result = await db.fetchrow(
        """INSERT INTO orders (cake_id, user_id, customization, delivery_date, delivery_address, status, total_price, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
           RETURNING id, cake_id, user_id, customization, delivery_date, delivery_address, status, total_price, created_at""",
        order.cake_id, current_user.id, customization_dict, order.delivery_date, order.delivery_address, 
        "processing", total_price, now)
    return models.Order(
        id=result["id"],
        cake_id=result["cake_id"],
        user_id=result["user_id"],
        customization=models.CakeCustomization(**result["customization"]),
        delivery_date=result["delivery_date"],
        delivery_address=result["delivery_address"],
        status=result["status"],
        total_price=result["total_price"],
        created_at=result["created_at"]
    )

# PUBLIC_INTERFACE
@router.get("/orders/history", response_model=List[models.OrderHistoryItem], summary="Order history", tags=["Order"])
async def order_history(db: Connection = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Get current user's order history.
    """
    orders = await db.fetch(
        "SELECT o.*, c.* FROM orders o JOIN cakes c ON o.cake_id = c.id WHERE o.user_id=$1 ORDER BY o.created_at DESC",
        current_user.id)
    history = []
    for row in orders:
        order = models.Order(
            id=row["id"],
            cake_id=row["cake_id"],
            user_id=row["user_id"],
            customization=models.CakeCustomization(**row["customization"]),
            delivery_date=row["delivery_date"],
            delivery_address=row["delivery_address"],
            status=row["status"],
            total_price=row["total_price"],
            created_at=row["created_at"]
        )
        cake = models.Cake(
            id=row["cake_id"],
            name=row["name"],
            description=row["description"],
            base_price=row["base_price"],
            image_url=row["image_url"],
            available_sizes=row["available_sizes"],
            available_flavors=row["available_flavors"],
            available_toppings=row["available_toppings"]
        )
        history.append(models.OrderHistoryItem(order=order, cake=cake))
    return history

# PUBLIC_INTERFACE
@router.get("/orders/{order_id}", response_model=models.Order, summary="Order tracking", tags=["Order"])
async def get_order(order_id: int, db: Connection = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Get a specific order and track status.
    """
    row = await db.fetchrow("SELECT * FROM orders WHERE id=$1 AND user_id=$2", order_id, current_user.id)
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    return models.Order(
        id=row["id"],
        cake_id=row["cake_id"],
        user_id=row["user_id"],
        customization=models.CakeCustomization(**row["customization"]),
        delivery_date=row["delivery_date"],
        delivery_address=row["delivery_address"],
        status=row["status"],
        total_price=row["total_price"],
        created_at=row["created_at"]
    )

# ---------------------------------------------------------------------------
# PUBLIC_INTERFACE
@router.post("/notifications/push", summary="Register for Push Notifications", tags=["Push Notification"])
async def subscribe_push(payload: models.PushSubscription, db: Connection = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Register user's device/browser for push notifications.
    """
    await db.execute("INSERT INTO push_subscriptions (user_id, endpoint, keys) VALUES ($1, $2, $3) ON CONFLICT (user_id, endpoint) DO UPDATE SET keys=$3", current_user.id, payload.endpoint, payload.keys)
    return {"result": "ok"}

# ---------------------------------------------------------------------------
# PUBLIC_INTERFACE
@router.post("/payments/stripe/create-intent", response_model=models.StripePaymentIntent, summary="Create Stripe PaymentIntent", tags=["Payment"])
async def create_payment_intent(order_id: int, db: Connection = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Create a Stripe PaymentIntent for the given order.
    """
    # Placeholder: Normally you'd call Stripe API here
    # For demo purposes, return a fake client secret
    return models.StripePaymentIntent(client_secret="stripe_dummy_client_secret_xyz")

# ---------------------------------------------------------------------------
# PUBLIC_INTERFACE
@router.get("/orders/{order_id}/status", response_model=dict, summary="Get Order Status", tags=["Order"])
async def get_order_status(order_id: int, db: Connection = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Get the current status of a specific order.
    """
    row = await db.fetchrow("SELECT status FROM orders WHERE id=$1 AND user_id=$2", order_id, current_user.id)
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order_id, "status": row["status"]}
