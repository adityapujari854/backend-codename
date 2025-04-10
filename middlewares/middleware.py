from fastapi import Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from auth.jwt_handler import verify_token

class JWTMiddleware(BaseHTTPMiddleware):
    """ ✅ Middleware for verifying Access JWT token in protected routes """

    async def dispatch(self, request: Request, call_next):
        # ✅ Define public routes that do NOT require authentication
        public_routes = [
            "/",
            "/api/auth/login",
            "/api/auth/signup",
            "/api/auth/refresh-token",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/api/services",
            "/api/providers"
        ]

        # ✅ Skip authentication for public routes
        if any(request.url.path.startswith(route) for route in public_routes):
            return await call_next(request)

        # ✅ Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization token missing or invalid")

        token = auth_header.split(" ")[1]

        try:
            # ✅ Verify Access Token
            user_email = verify_token(token, token_type="access")
            request.state.user = user_email  # Store user in request state
        except HTTPException as e:
            raise HTTPException(status_code=401, detail=e.detail)

        return await call_next(request)


# ✅ Helper function to extract user from header (for dependency injection)
def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or "Bearer " not in authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = authorization.split(" ")[1]
    return verify_token(token, token_type="access")


# ✅ Middleware Setup Function
def setup_middlewares(app):
    """ Applies CORS and JWT middlewares to the FastAPI app """

    # ✅ Add CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Replace with specific frontend domain in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ Add JWT Middleware
    app.add_middleware(JWTMiddleware)
