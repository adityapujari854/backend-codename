import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import auth_router  # ✅ Fix: Direct Import
from routes.providers import providers_router
from routes.bookings import bookings_router
from routes.services import services_router
from routes.send_email import email_router

# ✅ Function to Import Routes Safely
def safe_import(module_name, router_name):
    try:
        module = __import__(module_name, fromlist=[router_name])
        return getattr(module, router_name)
    except (ImportError, AttributeError) as e:
        print(f"⚠️ Warning: Could not import {module_name}.{router_name} - {e}")
        return None

# ✅ Import Middleware (If Available)
try:
    from middlewares.middleware import setup_middlewares
    middleware_available = True
except ImportError:
    middleware_available = False
    print("⚠️ Middleware module not found. Skipping middleware setup.")

# ✅ Import Routes (If Available)
# auth_router = safe_import("routes.auth_routes", "auth_router")  # ✅ Fixed import path
# bookings_router = safe_import("routes.bookings", "bookings_router")
# email_router = safe_import("routes.send_email", "email_router")
# services_router = safe_import("routes.services", "services_router")
# providers_router = safe_import("routes.providers", "providers_router")




# ✅ Initialize FastAPI App
app = FastAPI(
    title="Homezy API",
    version="1.0.0",
    description="API for Homezy Platform",
)

# ✅ Apply Middleware if available
if middleware_available:
    setup_middlewares(app)

# ✅ Enable CORS (Security: Change `allow_origins` in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔹 Replace "*" with frontend domain in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(bookings_router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(providers_router, prefix="/api/providers", tags=["Providers"])
app.include_router(services_router, prefix="/api/services", tags=["Services"])
app.include_router(email_router, prefix="/api/email", tags=["Email"])

# ✅ Include Routers (Only if Available)
if auth_router:
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    print("✅ Registered: /api/auth")

if bookings_router:
    app.include_router(bookings_router, prefix="/api/bookings", tags=["Bookings"])
    print("✅ Registered: /api/bookings")

if email_router:
    app.include_router(email_router, prefix="/api/email", tags=["Email"])
    print("✅ Registered: /api/email")

if services_router:
    app.include_router(services_router, prefix="/api/services", tags=["Services"])
    print("✅ Registered: /api/services")

if providers_router:
    app.include_router(providers_router, prefix="/api/providers", tags=["Providers"])
    print("✅ Registered: /api/providers")

# ✅ Root API Endpoint
@app.get("/", tags=["Root"])
def home():
    """🏠 Root API Endpoint"""
    return {"message": "Welcome to Homezy API!"}

# ✅ Run the FastAPI App
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # ✅ Set default port to 8000 if not specified
    print(f"🚀 Starting FastAPI server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
