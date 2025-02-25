from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from passlib.context import CryptContext
from typing import Optional

# ✅ Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ User Model for Signup
class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password (min 6 characters)")

    def hash_password(self):
        """Hashes the user's password before storing in DB."""
        self.password = pwd_context.hash(self.password)


# ✅ User Model for Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ✅ User Model in Database
class UserDB(BaseModel):
    name: str
    email: EmailStr
    password: str  # ✅ Already hashed password
    is_verified: bool = False  # ✅ User verification status
    otp_code: Optional[str] = None  # ✅ OTP code for verification
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ✅ OTP Verification Model
class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
