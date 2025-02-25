import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ Import Middleware Setup Function
from middlewares.middleware import setup_middlewares

# ✅ Importing Routers
from routes.auth import auth_router
from routes.bookings import bookings_router
from routes.send_email import email_router
from routes.services import services_router
from routes.providers import providers_router

# ✅ Initialize FastAPI App
app = FastAPI(
    title="Homezy API",
    version="1.0.0",
    description="API for Homezy Platform"
)

# ✅ Apply Middlewares
setup_middlewares(app)

# ✅ Enable CORS for Railway Hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Change this to specific frontend URL in production
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
    """🏠 Root API Endpoint"""
    return {"message": "Welcome to Homezy API!"}

# ✅ Run the app (Automatically runs in Railway)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Railway assigns a dynamic PORT
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)