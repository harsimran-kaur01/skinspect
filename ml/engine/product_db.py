"""
Product database – curated skincare products with details.
You can expand this list with real products and links.
"""

PRODUCTS = [
    # --- Cleansers ---
    {
        "name": "Salicylic Acid Cleanser",
        "category": "cleanser",
        "description": "Gentle daily cleanser to unclog pores and prevent breakouts.",
        "skin_types": ["oily", "combination"],
        "concerns": ["acne", "blackheads"],
        "severity": ["mild", "moderate"],
        "price_range": "budget",
        "key_ingredients": ["salicylic acid", "ceramides"],
        "link": "https://example.com/salicylic-cleanser",
        "fragrance_free": True,
        "vegan": False,
    },
    {
        "name": "Hydrating Cream Cleanser",
        "category": "cleanser",
        "description": "Non-stripping cleanser for dry or sensitive skin.",
        "skin_types": ["dry", "sensitive"],
        "concerns": ["dryness", "itchiness"],
        "severity": ["mild", "moderate"],
        "price_range": "budget",
        "key_ingredients": ["ceramides", "glycerin"],
        "link": "https://example.com/hydrating-cleanser",
        "fragrance_free": True,
        "vegan": True,
    },
    # --- Treatments ---
    {
        "name": "Benzoyl Peroxide Gel",
        "category": "treatment",
        "description": "Targeted spot treatment for active breakouts.",
        "skin_types": ["oily", "combination"],
        "concerns": ["acne"],
        "severity": ["moderate", "severe"],
        "price_range": "budget",
        "key_ingredients": ["benzoyl peroxide"],
        "link": "https://example.com/benzoyl-peroxide",
        "fragrance_free": True,
        "vegan": False,
    },
    {
        "name": "Centella Asiatica Serum",
        "category": "serum",
        "description": "Soothes irritation, redness, and supports skin barrier.",
        "skin_types": ["sensitive", "dry", "combination"],
        "concerns": ["itchiness", "redness", "sensitivity"],
        "severity": ["mild", "moderate"],
        "price_range": "mid-range",
        "key_ingredients": ["centella asiatica", "madecassoside"],
        "link": "https://example.com/centella-serum",
        "fragrance_free": True,
        "vegan": True,
    },
    # --- Moisturizers ---
    {
        "name": "Oil-Free Moisturizer",
        "category": "moisturizer",
        "description": "Lightweight hydration without clogging pores.",
        "skin_types": ["oily", "combination"],
        "concerns": ["oiliness", "acne"],
        "severity": [],
        "price_range": "budget",
        "key_ingredients": ["hyaluronic acid", "green tea"],
        "link": "https://example.com/oil-free-moisturizer",
        "fragrance_free": True,
        "vegan": True,
    },
    {
        "name": "Ceramide Moisturizer",
        "category": "moisturizer",
        "description": "Restores skin barrier and locks in moisture for dry skin.",
        "skin_types": ["dry", "sensitive"],
        "concerns": ["dryness", "itchiness", "sensitivity"],
        "severity": ["mild", "moderate"],
        "price_range": "mid-range",
        "key_ingredients": ["ceramides", "cholesterol"],
        "link": "https://example.com/ceramide-moisturizer",
        "fragrance_free": True,
        "vegan": False,
    },
    # --- Sunscreens ---
    {
        "name": "SPF 50+ Sunscreen",
        "category": "sunscreen",
        "description": "Broad-spectrum protection for daily use.",
        "skin_types": ["all"],
        "concerns": [],
        "severity": [],
        "price_range": "mid-range",
        "key_ingredients": ["zinc oxide", "titanium dioxide"],
        "link": "https://example.com/spf50-sunscreen",
        "fragrance_free": True,
        "vegan": True,
    },
    # --- Exfoliants ---
    {
        "name": "AHA/BHA Exfoliating Toner",
        "category": "exfoliant",
        "description": "Chemical exfoliation to improve texture and clarity.",
        "skin_types": ["oily", "combination", "normal"],
        "concerns": ["dullness", "blackheads"],
        "severity": ["mild", "moderate"],
        "price_range": "mid-range",
        "key_ingredients": ["glycolic acid", "salicylic acid"],
        "link": "https://example.com/aha-bha-toner",
        "fragrance_free": False,
        "vegan": True,
    },
]


def get_products_by_filters(
    skin_type=None,
    concerns=None,
    sensitivity_level=None,
    price_preference=None,
    fragrance_free=None,
    vegan=None,
    max_price=None,
):
    """Filter products based on multiple criteria."""
    results = []
    for p in PRODUCTS:
        # Skin type filter
        if skin_type and p.get("skin_types") and skin_type not in p["skin_types"]:
            continue
        # Concerns filter (if any, product must match at least one)
        if concerns:
            if not p.get("concerns"):
                continue
            if not any(c in p["concerns"] for c in concerns):
                continue
        # Sensitivity level – for sensitive, prefer fragrance-free and soothing
        if sensitivity_level in ["moderately sensitive", "very sensitive"]:
            if p.get("fragrance_free") is False:
                continue
            # Also prefer products with soothing ingredients (simple heuristic)
        # Price preference
        if price_preference and p.get("price_range") != price_preference:
            continue
        # Fragrance free
        if fragrance_free is not None and p.get("fragrance_free") != fragrance_free:
            continue
        # Vegan
        if vegan is not None and p.get("vegan") != vegan:
            continue
        results.append(p)
    return results
