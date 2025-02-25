from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importing Routers
from routes.auth import auth_router
from routes.bookings import bookings_router
from routes.send_email import email_router
from routes.services import services_router
from routes.providers import providers_router

# Import Middleware
try:
    from middlewares.middleware import get_current_user  # Ensure this exists!
except ImportError:
    get_current_user = None  # Handle missing middleware gracefully

app = FastAPI(title="Homezy API", version="1.0.0", description="API for Homezy Platform")

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Consider restricting this in production!
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ✅ Include Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(bookings_router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(email_router, prefix="/api/email", tags=["Email"])
app.include_router(services_router, prefix="/api/services", tags=["Services"])
app.include_router(providers_router, prefix="/api/providers", tags=["Providers"])

@app.get("/", tags=["Root"])
def home():
    return {"message": "Welcome to Homezy API!"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)