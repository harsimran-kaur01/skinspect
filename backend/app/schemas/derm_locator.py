from pydantic import BaseModel
from typing import Optional, List


class Location(BaseModel):
    lat: float
    lng: float


class DermClinic(BaseModel):
    name: str
    address: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    place_id: Optional[str] = None
    distance_km: Optional[float] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    vicinity: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class NearbyDermsResponse(BaseModel):
    clinics: List[DermClinic]
    total_results: int
    location: Location
    searched_radius_km: float
    # False if we couldn't find anything tagged as dermatology-specific
    # and had to fall back to general clinics/hospitals instead. The
    # frontend should tell the user this explicitly rather than silently
    # mixing dermatologists in with dementia care homes and vet clinics.
    is_dermatology_specific: bool
