from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional
import random

# ✅ Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Hash Password Function
def hash_password(password: str) -> str:
    """Hashes the user's password before storing it in the database."""
    return pwd_context.hash(password)

# ✅ User Model for Signup
class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password (min 6 characters)")

    def hashed_password(self):
        """Returns a hashed password for storage."""
        return hash_password(self.password)

# ✅ User Model for Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ✅ User Model in Database
class UserDB(BaseModel):
    name: str
    email: EmailStr
    password: str  # ✅ Hashed password
    is_verified: bool = False  # ✅ Email verification status
    otp_code: Optional[str] = None  # ✅ OTP code for verification
    otp_expiry: Optional[datetime] = None  # ✅ OTP expiry time
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def set_otp(self):
        """Generates a 6-digit OTP & expiry time."""
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=10)

# ✅ OTP Verification Model
class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
