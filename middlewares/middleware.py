from fastapi import Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from auth.jwt_handler import verify_jwt_token

# ✅ Middleware to Extract User from JWT Token
def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(status_code=401, detail="Authorization token missing or invalid")

    token = authorization.split(" ")[1]  # Extract token from "Bearer <token>"
    return verify_jwt_token(token)

class JWTMiddleware(BaseHTTPMiddleware):
    """ ✅ Middleware for verifying JWT token in requests """

    async def dispatch(self, request: Request, call_next):
        public_routes = ["/api/login", "/api/signup", "/docs", "/openapi.json"]
        if any(request.url.path.startswith(route) for route in public_routes):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization token missing or invalid")

        token = auth_header.split(" ")[1]

        try:
            user_email = verify_jwt_token(token)
            request.state.user = user_email
        except HTTPException as e:
            raise HTTPException(status_code=401, detail=str(e.detail))

        return await call_next(request)
