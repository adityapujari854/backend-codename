import os
import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List

# ✅ Load API Key from Environment Variables
FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
if not FOURSQUARE_API_KEY:
    raise ValueError("❌ ERROR: FOURSQUARE_API_KEY is not set in environment variables!")

# ✅ Initialize Router
providers_router = APIRouter(prefix="/api/providers", tags=["Service Providers"])

# ✅ Foursquare API Constants
FOURSQUARE_API_URL = "https://api.foursquare.com/v3/places/search"
HEADERS = {
    "Authorization": f"Bearer {FOURSQUARE_API_KEY}",
    "Accept": "application/json"
}

# ✅ Fetch service providers from Foursquare API
@providers_router.get("/", summary="Get service providers from Foursquare API")
async def get_providers(
    service_name: str = Query(..., title="Service Name"),
    city: str = Query("Pune", title="City"),
    limit: int = Query(10, le=20)
) -> Dict[str, Any]:
    """
    Fetch service providers based on a given service name and city using the Foursquare API.
    """

    # ✅ Debugging logs
    print(f"🔍 Incoming Request - service_name={service_name}, city={city}")

    # 🔥 FIX: Ensure service_name is formatted properly
    formatted_service_name = service_name.replace(" ", "+")  # Ensure spaces are URL-encoded

    params = {"query": formatted_service_name, "near": city, "limit": limit}

    try:
        response = requests.get(FOURSQUARE_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        print("✅ Foursquare API Response:", data)

        results = data.get("results", [])
        
        if not results:
            print("⚠️ No providers found in Foursquare API response.")
            raise HTTPException(status_code=404, detail="⚠️ No providers found for the given service.")

        # ✅ Process Foursquare data
        providers: List[Dict[str, str]] = [
            {
                "business_name": place.get("name", "Unknown"),
                "address": place.get("location", {}).get("formatted_address", "Not available"),
                "contact_number": place.get("tel", "N/A"),
                "website": place.get("website", "N/A"),
                "categories": [category["name"] for category in place.get("categories", [])]
            }
            for place in results
        ]

        print(f"✅ Providers Found: {len(providers)}")
        return {"providers": providers}

    except requests.exceptions.RequestException as req_err:
        print(f"❌ API Request Error: {req_err}")
        raise HTTPException(status_code=502, detail=f"External API request failed: {str(req_err)}")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
