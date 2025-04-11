import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ Import Router List from routes/__init__.py
from routes import routers

# ✅ Ensure Middleware Import Safety
try:
    from middlewares.middleware import setup_middlewares
    middleware_available = True
except ImportError:
    middleware_available = False
    print("⚠️ Middleware module not found. Skipping middleware setup.")

# ✅ Initialize FastAPI App
app = FastAPI(
    title="Homezy API",
    version="1.0.0",
    description="API for Homezy Platform",
)

# ✅ Apply Middleware if available
if middleware_available:
    setup_middlewares(app)

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Replace with allowed frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register All Routers from the list in routes/__init__.py
for router, prefix, tags in routers:
    app.include_router(router, prefix=prefix, tags=tags)

# ✅ Debugging: Print Registered Routes at Startup
print("\n✅ Registered API Routes:")
for _, prefix, tags in routers:
    print(f"  - {prefix} ({tags[0]})")
print("")

# ✅ Root API Endpoint
@app.get("/", tags=["Root"])
def home():
    return {"message": "Welcome to Homezy API!"}

# ✅ Debugging Endpoint
@app.get("/debug/routes", tags=["Debug"])
def get_registered_routes():
    return {
        "routes": [
            {"path": route.path, "name": route.name}
            for route in app.routes
        ]
    }

# ✅ Run the App
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting FastAPI server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
