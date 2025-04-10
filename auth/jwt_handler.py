import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Header
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Secret Keys
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", JWT_SECRET_KEY)  # fallback to main key

if not JWT_SECRET_KEY:
    raise ValueError("❌ JWT_SECRET_KEY is missing! Set it in .env")

# ✅ Algorithm
JWT_ALGORITHM = "HS256"

# ✅ Expiry Configs
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# ✅ Create Access Token
def create_access_token(email: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "exp": expiration,
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# ✅ Create Refresh Token
def create_refresh_token(email: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": email,
        "exp": expiration,
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)

# ✅ Generic Token Verifier
def verify_token(token: str, token_type: str = "access") -> str:
    try:
        secret = JWT_SECRET_KEY if token_type == "access" else JWT_REFRESH_SECRET_KEY
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != token_type:
            raise HTTPException(status_code=403, detail=f"❌ Token is not a {token_type} token.")
        
        return payload.get("sub")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail=f"❌ {token_type.title()} token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail=f"❌ Invalid {token_type} token.")

# ✅ Extract User from Authorization Header
def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="❌ Missing Authorization header.")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="❌ Invalid Authorization header format. Use: Bearer <token>")

    token = authorization.split(" ")[1]
    return verify_token(token, token_type="access")
