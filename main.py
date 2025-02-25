from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import auth_router
from routes.bookings import bookings_router
from routes.send_email import email_router
from routes.services import services_router
from routes.providers import providers_router
from routes.bookings import bookings_router
from middlewares.middleware import get_current_user 

app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/")
def home():
    return {"message": "Welcome to Homezy API!"}
