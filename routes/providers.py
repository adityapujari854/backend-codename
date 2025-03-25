import os
import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from urllib.parse import quote

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
@providers_router.get("/", summary="Get service providers from Foursquare")
async def get_providers(
    service_name: str = Query(..., title="Service Name"),
    city: str = Query("Pune", title="City"),
    limit: int = Query(10, le=20)
) -> Dict[str, Any]:
    """
    Fetch service providers based on a given service name and city using the Foursquare API.
    """

    # ✅ Strip "Service" suffix to match Foursquare API format
    if service_name.endswith("Service"):
        service_name = service_name.replace("Service", "").strip()

    # ✅ Encode the query properly to handle spaces
    encoded_query = quote(service_name)

    params = {
        "query": encoded_query,
        "near": city,
        "limit": limit
    }

    try:
        # ✅ Send request to Foursquare API
        response = requests.get(FOURSQUARE_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])

        if not results:
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

        return {"providers": providers}

    except requests.exceptions.RequestException as req_err:
        raise HTTPException(status_code=502, detail=f"External API request failed: {str(req_err)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
