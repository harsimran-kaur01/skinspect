"""
Product database for the SkinSpect recommendation engine.

Every product declares:
  targets         {condition: weight 0-1}  how strongly it addresses a condition
  family          used by the engine to avoid duplicates / conflicting actives
  strength        gentle | moderate | strong  (checked against user sensitivity)
  severity        [] = any, otherwise only counts when the condition is at one
                  of these severities
  time            am | pm | both | as_needed | weekly
  pregnancy_safe  conservative flag; anything doubtful is False
Replace the example.com links with real product pages when you have them.
"""


def _p(
    name,
    category,
    family,
    description,
    targets,
    skin_types,
    usage,
    strength="gentle",
    severity=None,
    time="both",
    price="mid-range",
    ingredients=None,
    pregnancy_safe=True,
    vegan=True,
    tags=None,
):
    slug = name.lower().replace(" ", "-").replace("+", "and").replace("%", "")
    return {
        "name": name,
        "category": category,
        "family": family,
        "description": description,
        "targets": targets,
        "concerns": list(targets),  # kept for backward compatibility
        "skin_types": skin_types,
        "usage": usage,
        "strength": strength,
        "severity": severity or [],
        "time": time,
        "price_range": price,
        "key_ingredients": ingredients or [],
        "pregnancy_safe": pregnancy_safe,
        "fragrance_free": True,
        "vegan": vegan,
        "tags": tags or [],
        "link": f"https://example.com/{slug}",
    }


PRODUCTS = [
    # ------------------------------------------------------------ cleansers
    _p(
        "Gentle Gel Cleanser",
        "cleanser",
        "cleanser",
        "Lightweight gel cleanser that removes oil and sunscreen without stripping.",
        {"oiliness": 0.4, "acne": 0.3, "blackheads": 0.2},
        ["oily", "combination", "normal"],
        "Morning and night: massage for 30-60 seconds, rinse with lukewarm water.",
        price="budget",
        ingredients=["glycerin", "zinc pca"],
    ),
    _p(
        "Salicylic Acid 2% Cleanser",
        "cleanser",
        "cleanser",
        "Wash-off BHA cleanser that clears pores and reduces blackheads and breakouts.",
        {"acne": 0.8, "blackheads": 0.8, "oiliness": 0.6, "texture": 0.3},
        ["oily", "combination"],
        "Once a day (evening) to start; leave on for 30 seconds before rinsing. "
        "Use a plain cleanser in the morning.",
        strength="moderate",
        severity=["mild", "moderate"],
        time="pm",
        price="budget",
        ingredients=["salicylic acid", "ceramides"],
        pregnancy_safe=False,
        tags=["bha"],
    ),
    _p(
        "Hydrating Cream Cleanser",
        "cleanser",
        "cleanser",
        "Non-stripping cream cleanser that keeps the skin barrier comfortable.",
        {"dryness": 0.5, "sensitivity": 0.5, "redness": 0.3, "wrinkles": 0.15},
        ["dry", "sensitive", "normal"],
        "Morning and night: massage onto damp skin, rinse with lukewarm water.",
        price="budget",
        ingredients=["ceramides", "glycerin"],
    ),
    # ----------------------------------------------------- treatments/serums
    _p(
        "Benzoyl Peroxide 2.5% Gel",
        "treatment",
        "bpo",
        "Targeted treatment that kills acne bacteria and reduces inflamed breakouts.",
        {"acne": 0.9, "blackheads": 0.3},
        ["oily", "combination", "normal"],
        "Thin layer on affected areas only, once a day in the morning. Let it dry "
        "fully - it can bleach towels and pillowcases.",
        strength="strong",
        severity=["moderate", "severe"],
        time="am",
        price="budget",
        ingredients=["benzoyl peroxide"],
    ),
    _p(
        "Adapalene 0.1% Gel",
        "treatment",
        "retinoid",
        "Over-the-counter retinoid that unclogs pores, calms acne and improves texture "
        "and fine lines over time.",
        {
            "acne": 0.9,
            "blackheads": 0.8,
            "wrinkles": 0.5,
            "texture": 0.6,
            "hyperpigmentation": 0.4,
        },
        ["oily", "combination", "normal"],
        "Pea-sized amount for the whole face at night. Start 2 nights a week for 2 "
        "weeks, then every other night, then nightly if there is no irritation.",
        strength="strong",
        time="pm",
        price="budget",
        ingredients=["adapalene"],
        pregnancy_safe=False,
    ),
    _p(
        "Retinol 0.3% Night Serum",
        "serum",
        "retinoid",
        "Encourages cell turnover to soften fine lines, even texture and fade marks.",
        {
            "wrinkles": 0.9,
            "texture": 0.6,
            "hyperpigmentation": 0.4,
            "dullness": 0.4,
            "acne": 0.3,
        },
        ["normal", "combination", "oily", "dry"],
        "Pea-sized amount at night on dry skin. Start 2 nights a week for 2 weeks, "
        "then every other night; build to nightly only if your skin stays calm.",
        strength="moderate",
        time="pm",
        ingredients=["retinol"],
        pregnancy_safe=False,
    ),
    _p(
        "Bakuchiol Serum",
        "serum",
        "retinoid_alt",
        "Plant-based, gentler alternative to retinol for fine lines and texture.",
        {"wrinkles": 0.5, "texture": 0.3, "hyperpigmentation": 0.2},
        ["all"],
        "Once or twice a day on clean skin, before moisturizer.",
        ingredients=["bakuchiol"],
        pregnancy_safe=False,
    ),
    _p(
        "Azelaic Acid 10% Serum",
        "serum",
        "azelaic",
        "Multi-tasker for breakouts, redness and dark marks that is gentle enough for "
        "sensitive skin.",
        {
            "acne": 0.7,
            "redness": 0.8,
            "hyperpigmentation": 0.8,
            "texture": 0.3,
            "blackheads": 0.3,
        },
        ["all"],
        "Once daily at first, moving to twice daily as tolerated. Mild tingling in the "
        "first 2 weeks is normal.",
        ingredients=["azelaic acid"],
    ),
    _p(
        "Niacinamide 5% Serum",
        "serum",
        "niacinamide",
        "Regulates oil, refines pores and supports the skin barrier.",
        {
            "oiliness": 0.8,
            "acne": 0.5,
            "texture": 0.5,
            "hyperpigmentation": 0.4,
            "redness": 0.3,
            "blackheads": 0.3,
        },
        ["all"],
        "After cleansing and before moisturizer, once or twice a day.",
        price="budget",
        ingredients=["niacinamide", "zinc"],
    ),
    _p(
        "Vitamin C 15% Serum",
        "serum",
        "vitc",
        "Antioxidant serum that brightens dark spots and supports collagen.",
        {"hyperpigmentation": 0.8, "dullness": 0.8, "wrinkles": 0.5},
        ["normal", "combination", "dry", "oily"],
        "Mornings on clean, dry skin, before moisturizer and sunscreen. Store away "
        "from light and heat.",
        strength="moderate",
        time="am",
        ingredients=["l-ascorbic acid", "ferulic acid"],
    ),
    _p(
        "Ascorbyl Glucoside Vitamin C Serum",
        "serum",
        "vitc",
        "Gentle, stable vitamin C for brightening when strong acids are too harsh.",
        {"hyperpigmentation": 0.6, "dullness": 0.6, "wrinkles": 0.3, "acne": 0.2},
        ["all"],
        "Mornings on clean skin, before moisturizer and sunscreen.",
        time="am",
        ingredients=["ascorbyl glucoside"],
    ),
    _p(
        "Centella Asiatica Serum",
        "serum",
        "soothing",
        "Calms redness and irritation and helps repair a stressed skin barrier.",
        {"redness": 0.8, "sensitivity": 0.8, "acne": 0.2, "dryness": 0.2},
        ["all"],
        "Morning and/or night after cleansing, before moisturizer.",
        ingredients=["centella asiatica", "madecassoside"],
    ),
    _p(
        "Hyaluronic Acid + B5 Serum",
        "serum",
        "hydrator",
        "Water-binding serum that plumps and hydrates without heaviness.",
        {"dryness": 0.8, "dullness": 0.3, "wrinkles": 0.3},
        ["all"],
        "Apply to damp skin, then seal with moisturizer.",
        price="budget",
        ingredients=["hyaluronic acid", "panthenol"],
    ),
    _p(
        "Peptide Firming Serum",
        "serum",
        "peptide",
        "Peptides that support firmness and soften the look of fine lines.",
        {"wrinkles": 0.6, "dryness": 0.3},
        ["all"],
        "Morning and night after cleansing, before moisturizer.",
        price="premium",
        ingredients=["copper peptides", "matrixyl"],
    ),
    _p(
        "Hydrocolloid Pimple Patches",
        "spot",
        "patch",
        "Absorbs fluid from whitehead-stage pimples and stops you picking.",
        {"acne": 0.6},
        ["all"],
        "Apply to a clean, dry pimple overnight; replace once it turns white.",
        severity=["mild", "moderate"],
        time="as_needed",
        price="budget",
        ingredients=["hydrocolloid"],
    ),
    _p(
        "Kaolin Clay Mask",
        "mask",
        "mask",
        "Weekly mask that absorbs excess oil and loosens blackheads.",
        {"oiliness": 0.6, "blackheads": 0.6, "acne": 0.2, "texture": 0.3},
        ["oily", "combination"],
        "1-2 times a week for 10 minutes, then rinse. Skip if skin feels tight.",
        strength="moderate",
        time="weekly",
        price="budget",
        ingredients=["kaolin", "bentonite"],
    ),
    _p(
        "Caffeine + Peptide Eye Cream",
        "eye",
        "eye",
        "Brightens the under-eye area and softens fine lines around the eyes.",
        {"dark_circles": 0.8, "wrinkles": 0.4},
        ["all"],
        "Tap a small amount around the orbital bone morning and night.",
        ingredients=["caffeine", "peptides"],
    ),
    # ------------------------------------------------------------ exfoliants
    _p(
        "Salicylic Acid 2% Leave-on Liquid",
        "exfoliant",
        "acid",
        "Oil-soluble BHA that clears pores, blackheads and rough texture.",
        {"blackheads": 0.9, "acne": 0.7, "oiliness": 0.5, "texture": 0.6},
        ["oily", "combination", "normal"],
        "2-3 nights a week on clean, dry skin, followed by moisturizer.",
        strength="moderate",
        time="pm",
        price="budget",
        ingredients=["salicylic acid"],
        pregnancy_safe=False,
        tags=["bha"],
    ),
    _p(
        "Lactic Acid 5% Exfoliant",
        "exfoliant",
        "acid",
        "Mild AHA that smooths texture, fades dullness and boosts radiance.",
        {"dullness": 0.7, "texture": 0.7, "hyperpigmentation": 0.5, "wrinkles": 0.4},
        ["normal", "dry", "combination"],
        "Twice a week at night on clean, dry skin; skip on nights you use a retinoid.",
        strength="moderate",
        time="pm",
        ingredients=["lactic acid"],
        tags=["aha"],
    ),
    _p(
        "PHA Gentle Exfoliating Toner",
        "exfoliant",
        "acid",
        "Very gentle exfoliation for texture and dullness, suitable for sensitive skin.",
        {"texture": 0.4, "dullness": 0.5},
        ["all"],
        "2-3 nights a week after cleansing.",
        time="pm",
        ingredients=["gluconolactone", "lactobionic acid"],
        tags=["pha"],
    ),
    # ----------------------------------------------------------- moisturizers
    _p(
        "Oil-Free Gel Moisturizer",
        "moisturizer",
        "moisturizer",
        "Lightweight hydration that will not clog pores.",
        {"oiliness": 0.5, "acne": 0.3, "dryness": 0.2},
        ["oily", "combination"],
        "Morning and night after serums.",
        price="budget",
        ingredients=["hyaluronic acid", "green tea"],
    ),
    _p(
        "Ceramide Barrier Cream",
        "moisturizer",
        "moisturizer",
        "Rich barrier-repair cream for dry, sensitive or treatment-irritated skin.",
        {"dryness": 0.8, "sensitivity": 0.7, "redness": 0.4},
        ["dry", "sensitive", "normal", "combination"],
        "Morning and night; use a slightly thicker layer at night.",
        ingredients=["ceramides", "cholesterol"],
        tags=["barrier"],
        vegan=False,
    ),
    _p(
        "Barrier Repair Gel-Cream",
        "moisturizer",
        "moisturizer",
        "Light gel-cream that repairs the barrier without feeling heavy.",
        {"redness": 0.4, "sensitivity": 0.5, "dryness": 0.4, "acne": 0.2},
        ["oily", "combination", "sensitive"],
        "Morning and night after serums.",
        price="budget",
        ingredients=["ceramides", "panthenol"],
        tags=["barrier"],
    ),
    _p(
        "Lightweight Peptide Lotion",
        "moisturizer",
        "moisturizer",
        "Everyday lotion with peptides for softness and early fine-line support.",
        {"wrinkles": 0.4, "dryness": 0.4, "dullness": 0.2},
        ["normal", "dry", "combination"],
        "Morning and night after serums.",
        ingredients=["peptides", "glycerin"],
    ),
    # ------------------------------------------------------------- sunscreens
    _p(
        "SPF 50 PA++++ Gel Sunscreen",
        "sunscreen",
        "sunscreen",
        "Non-greasy broad-spectrum sun protection for daily wear.",
        {"hyperpigmentation": 0.8, "wrinkles": 0.7, "acne": 0.1, "oiliness": 0.2},
        ["oily", "combination", "normal"],
        "Two finger-lengths for face and neck every morning; reapply every 2-3 hours "
        "when outdoors.",
        time="am",
        ingredients=["uv filters"],
    ),
    _p(
        "Mineral Zinc SPF 50 Sunscreen",
        "sunscreen",
        "sunscreen",
        "Zinc-based sunscreen that is kind to sensitive and reactive skin.",
        {"hyperpigmentation": 0.8, "wrinkles": 0.7, "redness": 0.4, "sensitivity": 0.4},
        ["dry", "sensitive", "normal", "combination"],
        "Two finger-lengths for face and neck every morning; reapply every 2-3 hours "
        "when outdoors.",
        time="am",
        ingredients=["zinc oxide", "titanium dioxide"],
    ),
]


def get_products_by_filters(
    skin_type=None,
    concerns=None,
    sensitivity_level=None,
    price_preference=None,
    fragrance_free=None,
    vegan=None,
    exclude_ingredients=None,
    max_price=None,
):
    """Simple filter helper (kept for backward compatibility)."""
    results = []
    exclude_terms = [i.lower() for i in (exclude_ingredients or [])]
    for p in PRODUCTS:
        skin_types = p.get("skin_types") or []
        if (
            skin_type
            and skin_types
            and "all" not in skin_types
            and skin_type not in skin_types
        ):
            continue
        if concerns and not any(c in p["concerns"] for c in concerns):
            continue
        if sensitivity_level in ["moderately sensitive", "very sensitive"]:
            if not p.get("fragrance_free"):
                continue
        if price_preference and p.get("price_range") != price_preference:
            continue
        if fragrance_free is not None and p.get("fragrance_free") != fragrance_free:
            continue
        if vegan is not None and p.get("vegan") != vegan:
            continue
        if exclude_terms:
            ings = [i.lower() for i in p.get("key_ingredients", [])]
            if any(t in i for i in ings for t in exclude_terms):
                continue
        results.append(p)
    return results
