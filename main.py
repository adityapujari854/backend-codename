import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ Import Routers
from routes.auth import auth_router  
from routes.providers import providers_router
from routes.bookings import bookings_router
from routes.services import services_router
from routes.send_email import email_router
from routes.mybooking import mybooking_router  # ✅ Correct import

# ✅ Ensure Middleware Import Safety
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(bookings_router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(providers_router, prefix="/api/providers", tags=["Providers"])
app.include_router(services_router, prefix="/api/services", tags=["Services"])
app.include_router(email_router, prefix="/api/email", tags=["Email"])
app.include_router(mybooking_router, prefix="/api/mybooking", tags=["MyBooking"])  # ✅ FIXED

# ✅ Debugging: Print Registered Routes at Startup
print("\n✅ Registered API Routes:")
print("  - /api/auth (Authentication)")
print("  - /api/bookings (User Bookings)")
print("  - /api/providers (Service Providers)")
print("  - /api/services (Available Services)")
print("  - /api/email (Email Notifications)")
print("  - /api/mybooking (User's Previous Bookings)\n")

# ✅ Root API Endpoint
@app.get("/", tags=["Root"])
def home():
    return {"message": "Welcome to Homezy API!"}

# ✅ Debugging Endpoint
@app.get("/debug/routes", tags=["Debug"])
def get_registered_routes():
    return {
        "routes": [
            {"path": route.path, "name": route.name}
            for route in app.routes
        ]
    }

# ✅ Run App
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting FastAPI server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
