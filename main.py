import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ Directly Import Routes
from routes.auth import auth_router  
from routes.providers import providers_router
from routes.bookings import bookings_router
from routes.services import services_router
from routes.send_email import email_router

# ✅ Function to Import Routes Safely (Keeps Original Functionality)
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
    allow_origins=["http://backend-codename-production.up.railway.app/api/services/",
                   "https://codename2025.vercel.app/"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ✅ Register Routes **ONLY ONCE** (Fixes Duplicate Registrations)
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(bookings_router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(providers_router, prefix="/api/providers", tags=["Providers"])  # 🔥 FIXED ROUTE
app.include_router(services_router, prefix="/api/services", tags=["Services"])
app.include_router(email_router, prefix="/api/email", tags=["Email"])

# ✅ Debugging: Print Registered Routes at Startup
print("\n✅ Registered API Routes:")
print("  - /api/auth (Authentication)")
print("  - /api/bookings (User Bookings)")
print("  - /api/providers (Service Providers)")  # 🔥 Debugging Route Fix
print("  - /api/services (Available Services)")
print("  - /api/email (Email Notifications)\n")

# ✅ Include Routers (Only if Available - Keeps Original Functionality)
if auth_router:
    print("✅ Registered: /api/auth")
if bookings_router:
    print("✅ Registered: /api/bookings")
if providers_router:
    print("✅ Registered: /api/providers")
if services_router:
    print("✅ Registered: /api/services")
if email_router:
    print("✅ Registered: /api/email")

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
