from pydantic import BaseModel, EmailStr

class OTPModel(BaseModel):
    email: EmailStr
    otp: str
    expires_at: str
