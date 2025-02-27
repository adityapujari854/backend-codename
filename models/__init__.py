# Import all models to ensure they are recognized when used in routes

from .service import Service
from .booking import Booking
from .user import UserDB, UserSignup, UserLogin, VerifyOTP
from .otp import OTPModel