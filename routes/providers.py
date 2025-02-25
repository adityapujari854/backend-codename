import os
import requests
from fastapi import APIRouter, HTTPException

FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY")
router = APIRouter()

@router.get("/providers")
def get_providers(service_name: str, city: str = "Pune"):
    headers = {"Authorization": FOURSQUARE_API_KEY, "Accept": "application/json"}
    params = {"query": service_name, "near": city, "limit": 10}

    try:
        response = requests.get("https://api.foursquare.com/v3/places/search", headers=headers, params=params)
        data = response.json()
        providers = [
            {
                "business_name": place["name"],
                "address": place["location"].get("formatted_address", "N/A"),
                "contact_number": place.get("tel", "N/A"),
                "website": place.get("website", ""),
            }
            for place in data.get("results", [])
        ]
        return {"providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
