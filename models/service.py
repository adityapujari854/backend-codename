from pydantic import BaseModel, Field
from typing import Optional


class Service(BaseModel):
    """Schema for a service in the Homezy platform."""

    name: str = Field(..., title="Service Name", description="Name of the service")
    description: str = Field(..., title="Service Description", description="Short description of the service")
    image: str = Field(..., title="Service Image URL", description="URL of the service image")
    price: Optional[float] = Field(None, title="Service Price", description="Base price for the service")
    category: Optional[str] = Field(None, title="Service Category", description="Category of the service (e.g., Plumbing, Electrical)")
    available: bool = Field(True, title="Availability", description="Indicates if the service is currently available")

    class Config:
        schema_extra = {
            "example": {
                "name": "Plumbing",
                "description": "Expert plumbing services for your home.",
                "image": "https://example.com/images/plumbing.jpg",
                "price": 500.0,
                "category": "Home Repair",
                "available": True,
            }
        }
