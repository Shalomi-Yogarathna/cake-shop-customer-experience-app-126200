from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

# OpenAPI tags metadata
openapi_tags = [
    {"name": "Auth", "description": "User authentication endpoints"},
    {"name": "Cake", "description": "Browse and get cake catalog"},
    {"name": "Order", "description": "Order placement, history, and tracking"},
    {"name": "Payment", "description": "Payment integration (Stripe)"},
    {"name": "Push Notification", "description": "Push notification endpoints"}
]

app = FastAPI(
    title="Cake Shop Backend",
    description="Backend API for Cake Shop Customer Experience app. Browse cakes, customize, order, pay, and track your cakes.",
    version="1.0.0",
    openapi_tags=openapi_tags
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
def health_check():
    """Check API health."""
    return {"message": "Healthy"}

app.include_router(router, prefix="")

