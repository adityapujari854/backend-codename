from pydantic import BaseModel, EmailStr
from datetime import datetime
from passlib.context import CryptContext

# ✅ Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ User Model for Signup
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str

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
    password: str
    is_verified: bool = False
    otp_code: str | None = None
    created_at: datetime = datetime.utcnow()

# ✅ OTP Verification Model
class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str
