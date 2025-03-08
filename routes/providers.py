import os
import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List

# ✅ Load API Key from Environment Variables
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
if not FOURSQUARE_API_KEY:
    raise ValueError("❌ ERROR: FOURSQUARE_API_KEY is not set in environment variables!")

# ✅ Initialize Router
providers_router = APIRouter(prefix="/api/providers", tags=["Service Providers"])  # 🔥 Fixed Route Prefix

# ✅ Foursquare API Constants
FOURSQUARE_API_URL = "https://api.foursquare.com/v3/places/search"
HEADERS = {
    "Authorization": f"Bearer {FOURSQUARE_API_KEY}",  # 🔥 Fixed Authorization Format
    "Accept": "application/json"
}

# ✅ Fetch service providers from Foursquare API
@providers_router.get("/", summary="Get service providers from Foursquare")
async def get_providers(
    service_name: str = Query(..., title="Service Name", description="Type of service required"),
    city: str = Query("Pune", title="City", description="City where the service is needed"),
    limit: int = Query(10, title="Limit", description="Max number of results to return", le=20)
) -> Dict[str, Any]:
    """
    Fetch service providers based on a given service name and city using the Foursquare API.
    """

    # ✅ Debugging logs to check input parameters
    print(f"🔍 API Request: service_name={service_name}, city={city}, limit={limit}")

    params = {"query": service_name, "near": city, "limit": limit}

    try:
        response = requests.get(FOURSQUARE_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()  # Raise HTTP error if response is not 2xx

        data = response.json()
        results = data.get("results", [])

        if not results:
            print("⚠️ No providers found in Foursquare API response.")
            raise HTTPException(status_code=404, detail="⚠️ No providers found for the given service.")

        # ✅ Process Foursquare data & structure it properly
        providers: List[Dict[str, str]] = [
            {
                "business_name": place.get("name", "Unknown"),
                "address": place.get("location", {}).get("formatted_address", "Address not available"),
                "contact_number": place.get("tel", "Contact not available"),
                "website": place.get("website", "N/A"),
                "categories": [category["name"] for category in place.get("categories", [])]  # 🔍 Fetch categories
            }
            for place in results
        ]

        print(f"✅ Providers Found: {len(providers)}")  # ✅ Debugging log
        return {"providers": providers}

    except requests.exceptions.RequestException as req_err:
        print(f"❌ API Request Error: {req_err}")
        raise HTTPException(status_code=502, detail=f"External API request failed: {str(req_err)}")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
