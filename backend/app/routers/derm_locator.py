from fastapi import APIRouter, Depends, Query
from ..services.derm_locator import fetch_nearest_dermatologists
from ..schemas.derm_locator import NearbyDermsResponse, Location
from ..auth.dependencies import get_current_active_user
from ..models.user import User

router = APIRouter(prefix="/api/derm-locator", tags=["dermatologist"])


@router.get("/nearby", response_model=NearbyDermsResponse)
async def get_nearby_dermatologists(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    current_user: User = Depends(get_current_active_user),
):
    clinics, searched_radius_km, is_derm_specific = await fetch_nearest_dermatologists(
        lat, lng
    )
    return NearbyDermsResponse(
        clinics=clinics,
        total_results=len(clinics),
        location=Location(lat=lat, lng=lng),
        searched_radius_km=round(searched_radius_km, 1),
        is_dermatology_specific=is_derm_specific,
    )
