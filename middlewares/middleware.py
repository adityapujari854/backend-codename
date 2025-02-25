from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from auth.jwt_handler import verify_jwt_token

class JWTMiddleware(BaseHTTPMiddleware):
    """ ✅ Middleware for verifying JWT token in requests """
    
    async def dispatch(self, request: Request, call_next):
        # ✅ Skip authentication for public routes
        public_routes = ["/api/auth/login", "/api/auth/signup", "/docs", "/openapi.json"]
        if any(request.url.path.startswith(route) for route in public_routes):
            return await call_next(request)
        
        # ✅ Extract authorization token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization token missing or invalid")

        token = auth_header.split(" ")[1]
        
        try:
            user_data = verify_jwt_token(token)
            request.state.user = user_data  # Store user data (email, ID, etc.) in request state
        except HTTPException as e:
            raise HTTPException(status_code=401, detail=str(e.detail))

        return await call_next(request)

def setup_middlewares(app):
    """ ✅ Function to apply middlewares to the FastAPI app """
    
    # ✅ Enable CORS for frontend-backend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Change to specific domains in production
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Access-Control-Allow-Origin"],
    )

    # ✅ Add JWT Authentication Middleware
    app.add_middleware(JWTMiddleware)