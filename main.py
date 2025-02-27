import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ Import Middleware Setup Function (Handle Missing Middleware Gracefully)
try:
    from middlewares.middleware import setup_middlewares
except ImportError:
    setup_middlewares = None  # Prevent crashes if middleware is missing
    print("⚠️ Middleware module not found. Skipping middleware setup.")

# ✅ Importing Routers (Handle Missing Modules Gracefully)
def safe_import(module_name, router_name):
    try:
        module = __import__(module_name, fromlist=[router_name])
        return getattr(module, router_name)
    except (ImportError, AttributeError) as e:
        print(f"⚠️ Warning: Could not import {module_name}.{router_name} - {e}")
        return None

# ✅ Import Routes (If Available)
auth_router = safe_import("routes.auth", "auth_router")
bookings_router = safe_import("routes.bookings", "bookings_router")
email_router = safe_import("routes.send_email", "email_router")
services_router = safe_import("routes.services", "services_router")
providers_router = safe_import("routes.providers", "providers_router")

# ✅ Initialize FastAPI App
app = FastAPI(
    title="Homezy API",
    version="1.0.0",
    description="API for Homezy Platform"
)

# ✅ Apply Middlewares (if available)
if setup_middlewares:
    setup_middlewares(app)

# ✅ Enable CORS for Railway Hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ✅ Include Routers (Only if they exist)
if auth_router:
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
if bookings_router:
    app.include_router(bookings_router, prefix="/api/bookings", tags=["Bookings"])
if email_router:
    app.include_router(email_router, prefix="/api/email", tags=["Email"])
if services_router:
    app.include_router(services_router, prefix="/api/services", tags=["Services"])
if providers_router:
    app.include_router(providers_router, prefix="/api/providers", tags=["Providers"])

# ✅ Root API Endpoint
@app.get("/", tags=["Root"])
def home():
    """🏠 Root API Endpoint"""
    return {"message": "Welcome to Homezy API!"}

# ✅ Run the app (Automatically runs in Railway)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Railway dynamically assigns a PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
