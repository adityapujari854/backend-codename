import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List

# ✅ Foursquare API Constants (Directly Using Key)
FOURSQUARE_API_KEY = "fsq3LYB6FD4cl0rKy+iRre2J6vX3OYbh/RT7ZBwx0wfb2C4="
FOURSQUARE_API_URL = "https://api.foursquare.com/v3/places/search"

# ✅ Headers with Correct Authorization Format
HEADERS = {
    "Authorization": FOURSQUARE_API_KEY,
    "Accept": "application/json"
}

# ✅ Initialize Router
providers_router = APIRouter(tags=["Service Providers"])

# ✅ Mapped Services to Filter Irrelevant Results
SERVICE_KEYWORDS = {
    "Plumbing Service": ["plumbing", "pipe repair", "leak", "faucet", "drain"],
    "Electrical Repair": ["electrician", "circuit repair", "wiring", "fuse"],
    "House Cleaning": ["cleaning", "maid", "housekeeping", "janitorial"],
    "Carpentry": ["carpenter", "woodwork", "furniture", "cabinet"],
    "AC Repair": ["AC repair", "air conditioning", "HVAC", "cooling"],
    "Pest Control": ["pest", "insect", "termite", "cockroach", "rodent"],
    "Home Painting": ["painting", "painter", "wall paint", "interior"],
    "Gardening": ["gardening", "lawn care", "planting", "landscaping"],
    "Car Repair": ["car repair", "mechanic", "auto service", "tire change"],
    "CCTV Installation": ["cctv", "camera", "security system", "surveillance"]
}

# ✅ Fetch service providers from Foursquare API
@providers_router.get("/", summary="Get service providers from Foursquare")
async def get_providers(
    service_name: str = Query(..., title="Service Name", description="Name of the service to search"),
    limit: int = Query(10, le=20, title="Limit", description="Number of providers to display (max: 20)")
) -> Dict[str, Any]:
    """
    Fetch service providers based on a given service name and city (Pune) using the Foursquare API.
    Ensures a minimum of 5-10 relevant providers are displayed.
    """

    # ✅ Debugging logs
    print(f"🔍 Incoming Request - service_name={service_name}, limit={limit}")

    # ✅ Foursquare Query Parameters (Fetch 30-50 initially to filter and meet the threshold)
    fetch_limit = max(limit * 3, 30)  # Fetch 3x the limit to ensure filtering doesn't reduce providers
    params = {
        "query": service_name,
        "near": "Pune",
        "limit": fetch_limit
    }

    try:
        # ✅ API Request
        response = requests.get(FOURSQUARE_API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        print("✅ Foursquare API Response:", data)

        # ✅ Extract Results
        results = data.get("results", [])

        if not results:
            print("⚠️ No providers found in Foursquare API response.")
            raise HTTPException(status_code=404, detail="⚠️ No providers found for the given service.")

        # ✅ Filter Results Based on Service Keywords
        keywords = SERVICE_KEYWORDS.get(service_name, [])
        
        relevant_providers: List[Dict[str, str]] = []
        fallback_providers: List[Dict[str, str]] = []

        for place in results:
            categories = [category["name"].lower() for category in place.get("categories", [])]

            provider = {
                "business_name": place.get("name", "Unknown"),
                    "address": place.get("location", {}).get("formatted_address", "Not available"),
                    "contact_number": place.get("tel", "N/A"),
                    "website": place.get("website", "N/A"),
                    "category": categories[0] if categories else "General",  # ✅ Assign first category
                    "latitude": str(place.get("geocodes", {}).get("main", {}).get("latitude", "N/A")),
                    "longitude": str(place.get("geocodes", {}).get("main", {}).get("longitude", "N/A")),
                    "rating": place.get("rating", "N/A"),
                    "price": place.get("price", {}).get("tier", "N/A")
            }

            # ✅ Classify Providers: Relevant vs Fallback
            if any(keyword in " ".join(categories) for keyword in keywords):
                relevant_providers.append(provider)
            else:
                fallback_providers.append(provider)

        # ✅ Ensure Minimum of 5-10 Providers
        final_providers = relevant_providers[:limit]

        # 🔥 Add Fallback Providers if less than 5 relevant ones
        if len(final_providers) < 5:
            needed = 5 - len(final_providers)
            final_providers.extend(fallback_providers[:needed])

        # ✅ Ensure 5-10 Providers are Displayed
        final_providers = final_providers[:max(5, min(limit, 10))]

        print(f"✅ Providers Found: {len(final_providers)}")
        return {"providers": final_providers}

    except requests.exceptions.RequestException as req_err:
        print(f"❌ API Request Error: {req_err}")
        raise HTTPException(status_code=502, detail=f"External API request failed: {str(req_err)}")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
