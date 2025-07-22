from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# ---------- User Models ----------

# PUBLIC_INTERFACE
class UserBase(BaseModel):
    """Base user information (public view)."""
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="User email")

# PUBLIC_INTERFACE
class UserCreate(UserBase):
    """User registration information."""
    password: str = Field(..., min_length=6, description="Password")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """User login credentials."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="Password")

# PUBLIC_INTERFACE
class User(UserBase):
    """User information with ID."""
    id: int

    class Config:
        orm_mode = True

# ---------- Cake Models ----------

# PUBLIC_INTERFACE
class CakeBase(BaseModel):
    """Basic cake information."""
    name: str
    description: str
    base_price: float

# PUBLIC_INTERFACE
class Cake(CakeBase):
    """Complete cake information."""
    id: int
    image_url: Optional[str]
    available_sizes: List[str]
    available_flavors: List[str]
    available_toppings: List[str]

    class Config:
        orm_mode = True

# ---------- Customization Models ----------

# PUBLIC_INTERFACE
class CakeCustomization(BaseModel):
    """Cake customization options selected by user."""
    size: str
    flavor: str
    toppings: List[str] = []

# ---------- Order Models ----------

# PUBLIC_INTERFACE
class OrderBase(BaseModel):
    """Order information (used for creation)."""
    cake_id: int
    customization: CakeCustomization
    delivery_date: datetime
    delivery_address: str

# PUBLIC_INTERFACE
class OrderCreate(OrderBase):
    """Order creation payload."""
    payment_method: str = Field(..., description="Method for payment, e.g., 'stripe'")

# PUBLIC_INTERFACE
class Order(OrderBase):
    """Order information including status and user."""
    id: int
    user_id: int
    status: str
    total_price: float
    created_at: datetime

    class Config:
        orm_mode = True

# ---------- History & Tracking ----------

# PUBLIC_INTERFACE
class OrderHistoryItem(BaseModel):
    """Single order for user's history."""
    order: Order
    cake: Cake

# ---------- Push Notification ----------

# PUBLIC_INTERFACE
class PushSubscription(BaseModel):
    """Push notification subscription information."""
    endpoint: str
    keys: dict

# ---------- Stripe Payment Placeholder ----------

# PUBLIC_INTERFACE
class StripePaymentIntent(BaseModel):
    """Stripe payment intent placeholder."""
    client_secret: str
