import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Secret Key for JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_TIME_MINUTES = 60 * 24  # 1 Day Token Expiry

# ✅ Function to Create JWT Token
def create_jwt_token(email: str) -> str:
    expiration = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_TIME_MINUTES)
    payload = {"sub": email, "exp": expiration}
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

# ✅ Function to Verify JWT Token
def verify_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload["sub"]  # Return the email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Middleware to Extract User from JWT Token
def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid format")

    token = authorization.split(" ")[1]  # Extract token from "Bearer <token>"
    return verify_jwt_token(token)
