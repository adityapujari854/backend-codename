from pydantic import BaseModel, Field
from typing import Optional, List

class Service(BaseModel):
    """Schema for a service in the Homezy platform."""

    name: str = Field(..., title="Service Name", description="Name of the service")
    description: str = Field(..., title="Service Description", description="Short description of the service")
    image: str = Field(..., title="Service Image URL", description="URL of the service image")
    price: Optional[float] = Field(None, title="Service Price", description="Base price for the service")
    categories: Optional[List[str]] = Field(None, title="Service Categories", description="List of subcategories under this service (e.g., Fan, Wiring, Doorbell)")
    available: bool = Field(True, title="Availability", description="Indicates if the service is currently available")

    class Config:
        schema_extra = {
            "example": {
                "name": "Electrical",
                "description": "Professional electrical services for your home.",
                "image": "https://example.com/images/electrical.jpg",
                "price": 1000.0,
                "categories": ["Fan Installation", "Wiring Repair", "Doorbell Fix"],
                "available": True,
            }
        }
