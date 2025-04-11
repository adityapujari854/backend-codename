from .auth import auth_router
from .bookings import bookings_router
from .send_email import email_router
from .services import services_router
from .providers import providers_router
from .mybooking import mybooking_router

# ✅ List all routers to be used in `main.py`
routers = [
    (auth_router, "/api/auth", ["Auth"]),
    (bookings_router, "/api/bookings", ["Bookings"]),
    (email_router, "/api/email", ["Email"]),
    (services_router, "/api/services", ["Services"]),
    (providers_router, "/api/providers", ["Providers"]),
    (mybooking_router, "/api/mybooking", ["MyBookings"]),
]
