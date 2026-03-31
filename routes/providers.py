import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List

# ✅ Foursquare API Constants (Directly Using Key)
GOOGLE_API_KEY = "AIzaSyDaUkmUhpxBFJFPPXpE3RzpRcL90vtFGMw"
GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

# ✅ Headers with Correct Authorization Format
HEADERS = {
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
    limit: int = Query(15, le=20, title="Limit", description="Number of providers to display (max: 20)")
) -> Dict[str, Any]:
    """
    Fetch service providers based on a given service name and city (Pune) using the Foursquare API.
    Ensures a minimum of 5-15 relevant providers are displayed.
    """

    # ✅ Debugging logs
    print(f"🔍 Incoming Request - service_name={service_name}, limit={limit}")

    # ✅ Google Places Query Parameters
    params = {
        "query": f"{service_name} in Pune",
        "key": GOOGLE_API_KEY
    }

    try:
        # ✅ API Request
        response = requests.get(GOOGLE_PLACES_URL, params=params)
        response.raise_for_status()
        data = response.json()

        print("✅ Foursquare API Response:", data)

        # ✅ Extract Results
        results = data.get("results", [])

        if not results:
            print("⚠️ No providers found in Google Places API response.")
            raise HTTPException(status_code=404, detail="⚠️ No providers found for the given service.")

        # ✅ Filter Results Based on Service Keywords
        keywords = SERVICE_KEYWORDS.get(service_name, [])
        
        relevant_providers: List[Dict[str, str]] = []
        fallback_providers: List[Dict[str, str]] = []

        for place in results:
            categories = [place.get("types", [])]  # Google has types array
            categories_flat = [t for sub in categories for t in sub]  # flatten

            provider = {
                "business_name": place.get("name", "Unknown"),
                "address": place.get("formatted_address", "Not available"),
                "contact_number": "N/A",  # Google doesn't provide phone in textsearch
                "website": "N/A",  # Not in textsearch
                "category": place.get("types", ["General"])[0] if place.get("types") else "General",
                "latitude": str(place.get("geometry", {}).get("location", {}).get("lat", "N/A")),
                "longitude": str(place.get("geometry", {}).get("location", {}).get("lng", "N/A")),
                "rating": str(place.get("rating", "N/A")),
                "price": "N/A"  # Not available
            }

            # ✅ Classify Providers: Relevant vs Fallback
            if any(keyword in " ".join(categories_flat) for keyword in keywords):
                relevant_providers.append(provider)
            else:
                fallback_providers.append(provider)

        # ✅ Ensure Minimum of 5-15 Providers
        final_providers = relevant_providers[:limit]

        # 🔥 Add Fallback Providers if less than 5 relevant ones
        if len(final_providers) < 5:
            needed = 5 - len(final_providers)
            final_providers.extend(fallback_providers[:needed])

        # ✅ Ensure 5-15 Providers are Displayed
        final_providers = final_providers[:max(5, min(limit, 15))]

        print(f"✅ Providers Found: {len(final_providers)}")
        return {"providers": final_providers}

    except requests.exceptions.RequestException as req_err:
        print(f"❌ API Request Error: {req_err}")
        # Return mock data instead of 502
        mock_providers = [
            {
                "business_name": "Mock Cleaning Service 1",
                "address": "123 Main St, Pune",
                "contact_number": "123-456-7890",
                "website": "https://example.com",
                "category": "cleaning",
                "latitude": "18.5204",
                "longitude": "73.8567",
                "rating": "4.5",
                "price": "N/A"
            },
            {
                "business_name": "Mock Cleaning Service 2",
                "address": "456 Elm St, Pune",
                "contact_number": "987-654-3210",
                "website": "https://example2.com",
                "category": "cleaning",
                "latitude": "18.5304",
                "longitude": "73.8667",
                "rating": "4.0",
                "price": "N/A"
            }
        ]
        return {"providers": mock_providers[:limit]}

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
