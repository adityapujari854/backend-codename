from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class Service(BaseModel):
    """Schema for a service in the Homezy platform."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Plumbing",
                "description": "Expert plumbing services for your home.",
                "image": "https://example.com/images/plumbing.jpg",
                "category": "Home Repair",
                "available": True,
            }
        }
    )

    name: str = Field(..., title="Service Name", description="Name of the service")
    description: str = Field(..., title="Service Description", description="Short description of the service")
    image: str = Field(..., title="Service Image URL", description="URL of the service image")
    category: Optional[str] = Field(None, title="Service Category", description="Category of the service (e.g., Plumbing, Electrical)")
    available: bool = Field(True, title="Availability", description="Indicates if the service is currently available")
