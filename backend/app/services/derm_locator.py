import httpx
import math
import time
from typing import List, Dict, Tuple
import logging

from ..schemas.derm_locator import DermClinic

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Kept deliberately modest — the previous version could expand up to
# 300km across TWO separate full search loops (dermatology-specific,
# then a general fallback), which meant up to ~14 sequential calls to a
# slow, rate-limited public API. That's what caused the 3-4 minute hang.
#
# This version does ONE combined query per radius step (fetches both
# dermatology-tagged AND general clinics/hospitals together, then
# classifies them client-side), and caps both the radius and the number
# of expansion steps much more tightly.
STARTING_RADIUS_KM = 10.0
MAX_SEARCH_RADIUS_KM = 60.0
EXPANSION_MULTIPLIER = 2.5  # fewer, bigger jumps instead of many small ones
DEFAULT_TARGET_RESULTS = 6  # stop as soon as we have "enough", not 10+
DEFAULT_MAX_RESULTS = 15
REQUEST_TIMEOUT_S = 12.0  # fail faster on a slow/overloaded Overpass mirror

# Simple in-memory cache so repeated requests for roughly the same
# location (e.g. reloading the page while testing) don't re-hit the
# public Overpass API every time. Keyed at ~1km precision. This is a
# process-local cache (resets on server restart) — fine for this use
# case, no need for Redis here.
_cache: Dict[Tuple[float, float], Tuple[float, list, float, bool]] = {}
_CACHE_TTL_S = 3600  # 1 hour


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _is_dermatology_tagged(tags: Dict[str, str]) -> bool:
    speciality = tags.get("healthcare:speciality", "").lower()
    name = tags.get("name", "").lower()
    if "dermatology" in speciality:
        return True
    if "derma" in name or "skin" in name:
        return True
    return False


def _build_combined_query(lat, lng, radius_m):
    """
    Single query that pulls both dermatology-relevant AND general
    clinic/hospital nodes in one Overpass call. We classify each result
    as dermatology-specific or not client-side (_is_dermatology_tagged)
    rather than running two separate full queries/expansion loops.
    """
    return f"""
    [out:json][timeout:20];
    (
      node["healthcare:speciality"~"dermatology",i](around:{radius_m},{lat},{lng});
      node["healthcare"="doctor"](around:{radius_m},{lat},{lng});
      node["amenity"="clinic"](around:{radius_m},{lat},{lng});
      node["amenity"="hospital"](around:{radius_m},{lat},{lng});
    );
    out center;
    """


async def _query_overpass(query: str) -> List[Dict]:
    headers = {
        "User-Agent": "SkinSpect/1.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
        try:
            response = await client.post(
                OVERPASS_URL, data={"data": query}, headers=headers
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning(f"Overpass request failed/timed out: {e}")
            return []
    return data.get("elements", [])


def _parse_clinics(
    elements: List[Dict], lat: float, lng: float, radius_km: float
) -> Tuple[List[DermClinic], List[DermClinic]]:
    """Returns (dermatology_specific, general) — both sorted by distance."""
    derm_specific = []
    general = []
    seen = set()

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "Unnamed Clinic")

        if "lat" in el and "lon" in el:
            el_lat, el_lon = el["lat"], el["lon"]
        elif "center" in el:
            el_lat, el_lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue

        distance_km = haversine(lat, lng, el_lat, el_lon)
        if distance_km > radius_km:
            continue

        dedupe_key = (name.strip().lower(), round(el_lat, 4), round(el_lon, 4))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        clinic = DermClinic(
            name=name,
            address=_format_address(tags),
            rating=None,
            user_ratings_total=None,
            place_id=str(el.get("id", "")),
            distance_km=round(distance_km, 2),
            phone=tags.get("phone", tags.get("contact:phone", "")),
            website=tags.get("website", tags.get("contact:website", "")),
            opening_hours=tags.get("opening_hours", ""),
            vicinity=tags.get("addr:street", ""),
            lat=el_lat,
            lng=el_lon,
        )

        if _is_dermatology_tagged(tags):
            derm_specific.append(clinic)
        else:
            general.append(clinic)

    derm_specific.sort(key=lambda c: c.distance_km)
    general.sort(key=lambda c: c.distance_km)
    return derm_specific, general


async def fetch_nearest_dermatologists(
    lat: float,
    lng: float,
    target_results: int = DEFAULT_TARGET_RESULTS,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> Tuple[List[DermClinic], float, bool]:
    """
    Returns (clinics, searched_radius_km, is_dermatology_specific).

    Runs ONE combined query per radius step (not two separate loops),
    expanding at most a few times, capped at MAX_SEARCH_RADIUS_KM.
    Prefers dermatology-specific results; only mixes in general
    clinics/hospitals if there aren't enough specific ones, and flags
    the response accordingly.
    """
    cache_key = (round(lat, 2), round(lng, 2))
    cached = _cache.get(cache_key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_S:
        _, clinics, radius, is_specific = cached
        return clinics, radius, is_specific

    current_radius = STARTING_RADIUS_KM
    derm_specific: List[DermClinic] = []
    general: List[DermClinic] = []

    while True:
        query = _build_combined_query(lat, lng, int(current_radius * 1000))
        elements = await _query_overpass(query)
        derm_specific, general = _parse_clinics(elements, lat, lng, current_radius)

        if (
            len(derm_specific) >= target_results
            or current_radius >= MAX_SEARCH_RADIUS_KM
        ):
            break

        current_radius = min(
            current_radius * EXPANSION_MULTIPLIER, MAX_SEARCH_RADIUS_KM
        )

    if derm_specific:
        result = derm_specific[:max_results]
        is_specific = True
    elif general:
        result = general[:max_results]
        is_specific = False
    else:
        result = []
        is_specific = True  # nothing found either way; flag is moot

    _cache[cache_key] = (time.time(), result, current_radius, is_specific)
    return result, current_radius, is_specific


def _format_address(tags: Dict[str, str]) -> str:
    if tags.get("addr:full"):
        return tags["addr:full"]

    parts = []
    house_street = " ".join(
        p for p in [tags.get("addr:housenumber"), tags.get("addr:street")] if p
    )
    if house_street:
        parts.append(house_street)
    if tags.get("addr:city"):
        parts.append(tags["addr:city"])
    if tags.get("addr:postcode"):
        parts.append(tags["addr:postcode"])

    return ", ".join(parts) if parts else tags.get("addr:street", "")
