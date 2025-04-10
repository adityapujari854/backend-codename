import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Secret Key for JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("❌ JWT_SECRET_KEY is missing! Please set it in your .env file.")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_TIME_MINUTES = int(os.getenv("JWT_EXPIRATION_TIME_MINUTES", 1440))  # Default: 1 Day (1440 minutes)

# ✅ Function to Create JWT Token
def create_jwt_token(email: str) -> str:
    """Generate JWT token with user email as subject"""
    expiration = datetime.now(datetime.timezone.utc) + timedelta(minutes=JWT_EXPIRATION_TIME_MINUTES)
    payload = {"sub": email, "exp": expiration}
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# ✅ Function to Verify JWT Token
def verify_jwt_token(token: str) -> str:
    """Verify JWT token and return the user's email"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")  # Return the email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="❌ Token has expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="❌ Invalid token. Please provide a valid JWT.")

# ✅ Middleware to Extract User from JWT Token
def get_current_user(authorization: str = Header(None)) -> str:
    """Extract and verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="❌ Missing Authorization header.")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="❌ Invalid Authorization header format. Use: Bearer <token>")

    token = authorization.split(" ")[1]  # Extract token from "Bearer <token>"
    return verify_jwt_token(token)
