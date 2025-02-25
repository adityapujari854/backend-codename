from fastapi import APIRouter, HTTPException, Query
import os
import requests

# ✅ Load API Key from Environment Variables
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")

if not FOURSQUARE_API_KEY:
    raise ValueError("❌ FOURSQUARE_API_KEY is not set in the environment variables!")

# ✅ Initialize Router
providers_router = APIRouter()

# ✅ Fetch service providers from Foursquare API
@providers_router.get("/")
def get_providers(service_name: str = Query(..., title="Service Name"), city: str = "Pune"):
    """Fetch service providers for a given service name using the Foursquare API."""
    
    headers = {"Authorization": FOURSQUARE_API_KEY, "Accept": "application/json"}
    params = {"query": service_name, "near": city, "limit": 10}

    try:
        response = requests.get("https://api.foursquare.com/v3/places/search", headers=headers, params=params)
        data = response.json()

        if "results" not in data:
            raise HTTPException(status_code=500, detail="Invalid response from Foursquare API")

        providers = [
            {
                "business_name": place["name"],
                "address": place["location"].get("formatted_address", "Address not available"),
                "contact_number": place.get("tel", "Contact not available"),
                "website": place.get("website", ""),
            }
            for place in data.get("results", [])
        ]

        return {"providers": providers}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching providers: {str(e)}")
