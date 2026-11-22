from fastapi import Request, HTTPException, Header
from starlette.middleware.base import BaseHTTPMiddleware
from auth.jwt_handler import verify_jwt_token

class JWTMiddleware(BaseHTTPMiddleware):
    """ ✅ Middleware for verifying JWT token in protected routes """

    async def dispatch(self, request: Request, call_next):
        # ✅ Define public routes that do NOT require authentication
        public_routes = [
            "/",
            "/api/auth/login",
            "/api/auth/signup",
            "/docs",
            "/openapi.json",
            "/favicon.ico",  # ✅ Allow requests for the browser favicon
            "/api/services",  # ✅ If service listings should be public
            "/api/providers"  # ✅ If provider search should be public
        ]
        
        # ✅ Skip authentication for public routes
        if any(request.url.path.startswith(route) for route in public_routes):
            return await call_next(request)

        # ✅ Extract authorization token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return HTTPException(status_code=401, detail="Authorization token missing or invalid")

        token = auth_header.split(" ")[1]

        try:
            user_email = verify_jwt_token(token)
            request.state.user = user_email  # Store user email in request state
        except HTTPException as e:
            raise HTTPException(status_code=401, detail=str(e.detail))

        return await call_next(request)


# ✅ Function to Extract User from JWT Token (Used in Routes)
def get_current_user(authorization: str = Header(None)) -> str:
    """ ✅ Extracts and verifies user from JWT Token """
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid format")

    token = authorization.split(" ")[1]  # Extract token from "Bearer <token>"
    return verify_jwt_token(token)


def setup_middlewares(app):
    """ ✅ Function to apply middlewares to the FastAPI app """
    app.add_middleware(JWTMiddleware)
