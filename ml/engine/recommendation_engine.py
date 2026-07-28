"""
Rule‑based recommendation engine that uses both scan results and MCQ questionnaire.
"""

import logging
from typing import Dict, List, Optional
from .product_db import get_products_by_filters

logger = logging.getLogger(__name__)


def generate_recommendations(scan_result: Dict, questionnaire: Dict) -> Dict:
    """
    Main entry point.

    Args:
        scan_result: dict from inference (skin_conditions, overall_health_score, skin_type, etc.)
        questionnaire: dict with structured MCQ answers

    Returns:
        dict with:
          - recommendations (list)
          - progress_summary (if previous scan provided)
          - overall_health_score
          - skin_type
    """
    # Extract questionnaire fields (with defaults)
    skin_type = questionnaire.get("skin_type") or scan_result.get(
        "skin_type", "combination"
    )
    concerns = questionnaire.get("concerns", [])
    sensitivity_level = questionnaire.get("sensitivity_level", "not sensitive")
    age_group = questionnaire.get("age_group")
    routine_complexity = questionnaire.get("routine_complexity", "basic")
    active_ingredients = questionnaire.get("active_ingredients", [])
    exfoliation_freq = questionnaire.get("exfoliation_freq", "never")
    sunscreen_use = questionnaire.get("sunscreen_use", "never")
    sun_exposure = questionnaire.get("sun_exposure", "indoors")
    price_preference = questionnaire.get("price_preference", "mid-range")
    fragrance_preference = questionnaire.get("fragrance_preference", "no preference")
    ethical_preference = questionnaire.get("ethical_preference", "no preference")
    stress_level = questionnaire.get("stress_level", "moderate")
    sleep_hours = questionnaire.get("sleep_hours", "7-8")
    water_intake = questionnaire.get("water_intake", "1-2L")
    smoking = questionnaire.get("smoking", "no")
    alcohol_freq = questionnaire.get("alcohol_freq", "occasionally")

    # Extract scan conditions
    conditions = scan_result.get("skin_conditions", [])
    active_conditions = []
    for c in conditions:
        if c.get("severity") not in ["none", None] and c.get("confidence", 0) > 0.4:
            active_conditions.append(
                {"condition": c["condition"], "severity": c.get("severity", "mild")}
            )

    # ==============================================
    # 1. PRODUCT RECOMMENDATIONS (from product_db)
    # ==============================================
    product_recs = []
    # For each active condition, get relevant products
    for ac in active_conditions:
        cond = ac["condition"]
        severity = ac["severity"]
        # Build filter
        prods = get_products_by_filters(
            skin_type=skin_type,
            concerns=[cond],
            sensitivity_level=sensitivity_level,
            price_preference=price_preference,
            fragrance_free=(fragrance_preference == "yes"),
            vegan=(ethical_preference == "yes")
            if ethical_preference != "no preference"
            else None,
        )
        # Optionally limit by severity (if product has severity field)
        for p in prods:
            # If product has severity list, check if severity matches
            if p.get("severity") and severity not in p["severity"]:
                continue
            product_recs.append(
                {
                    "type": "product",
                    "category": p["category"],
                    "title": p["name"],
                    "description": p["description"],
                    "priority": "high"
                    if severity in ["severe", "moderate"]
                    else "medium",
                    "product_details": {
                        "brand": "SkinSpect",
                        "price_range": p.get("price_range", "mid-range"),
                        "key_ingredients": p.get("key_ingredients", []),
                        "link": p.get("link", ""),
                    },
                }
            )

    # Ensure we have at least a moisturizer for the skin type
    if not any(r.get("category") == "moisturizer" for r in product_recs):
        moists = get_products_by_filters(
            skin_type=skin_type,
            concerns=[],
            sensitivity_level=sensitivity_level,
            price_preference=price_preference,
        )
        # Pick first moisturizer
        if moists:
            p = moists[0]
            product_recs.append(
                {
                    "type": "product",
                    "category": p["category"],
                    "title": p["name"],
                    "description": p["description"],
                    "priority": "medium",
                    "product_details": {
                        "brand": "SkinSpect",
                        "price_range": p.get("price_range", "mid-range"),
                        "key_ingredients": p.get("key_ingredients", []),
                        "link": p.get("link", ""),
                    },
                }
            )

    # ==============================================
    # 2. ROUTINE RECOMMENDATIONS (based on conditions and routine complexity)
    # ==============================================
    routine_recs = []
    if any(c["condition"] == "acne" for c in active_conditions):
        routine_recs.append(
            {
                "type": "routine",
                "title": "Acne Care Routine",
                "description": "Cleanse twice daily with salicylic acid cleanser. Use benzoyl peroxide spot treatment on active breakouts. Apply oil‑free moisturizer. Always wear sunscreen.",
                "priority": "high",
                "category": "routine",
            }
        )
    if any(c["condition"] == "wrinkles" for c in active_conditions):
        routine_recs.append(
            {
                "type": "routine",
                "title": "Anti‑Aging Routine",
                "description": "Use retinol at night (start slow), vitamin C in the morning, and always apply sunscreen.",
                "priority": "high"
                if age_group in ["35-44", "45-54", "55+"]
                else "medium",
                "category": "routine",
            }
        )

    # ==============================================
    # 3. LIFESTYLE RECOMMENDATIONS
    # ==============================================
    lifestyle_recs = []

    # Sunscreen reminder
    if sunscreen_use in ["rarely", "never"] and sun_exposure != "mostly indoors":
        lifestyle_recs.append(
            {
                "type": "lifestyle",
                "title": "Wear Sunscreen Daily",
                "description": f"With {sun_exposure} sun exposure, SPF is essential. Apply every morning, reapply if outdoors.",
                "priority": "high",
                "category": "sunscreen",
            }
        )

    # Stress management
    if stress_level == "high":
        lifestyle_recs.append(
            {
                "type": "lifestyle",
                "title": "Manage Stress",
                "description": "Stress can worsen skin conditions. Try meditation, exercise, or deep breathing.",
                "priority": "medium",
                "category": "wellness",
            }
        )

    # Hydration
    if water_intake in ["less than 1L", "1-2L"]:
        lifestyle_recs.append(
            {
                "type": "lifestyle",
                "title": "Stay Hydrated",
                "description": "Drinking enough water supports skin health. Aim for 2-3L daily.",
                "priority": "low",
                "category": "wellness",
            }
        )

    # Smoking/Alcohol
    if smoking in ["yes", "occasionally"]:
        lifestyle_recs.append(
            {
                "type": "lifestyle",
                "title": "Reduce Smoking/Vaping",
                "description": "Smoking accelerates aging and impairs skin healing. Consider reducing.",
                "priority": "high",
                "category": "wellness",
            }
        )
    if alcohol_freq in ["weekly", "daily"]:
        lifestyle_recs.append(
            {
                "type": "lifestyle",
                "title": "Moderate Alcohol",
                "description": "Excessive alcohol can dehydrate skin and worsen redness. Limit intake.",
                "priority": "medium",
                "category": "wellness",
            }
        )

    # ==============================================
    # 4. COMBINE AND SORT
    # ==============================================
    all_recs = product_recs + routine_recs + lifestyle_recs

    # Remove duplicates (by title)
    seen = set()
    unique_recs = []
    for r in all_recs:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique_recs.append(r)

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    unique_recs.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 1))

    # ==============================================
    # 5. PROGRESS TRACKING
    # ==============================================
    progress = None
    previous_scan = questionnaire.get("previous_scan")
    if previous_scan and "overall_health_score" in previous_scan:
        prev_score = previous_scan["overall_health_score"]
        current_score = scan_result.get("overall_health_score", 0)
        diff = current_score - prev_score
        if diff > 5:
            trend = "improved"
        elif diff < -5:
            trend = "declined"
        else:
            trend = "stable"
        progress = {
            "score_change": diff,
            "trend": trend,
            "previous_score": prev_score,
            "current_score": current_score,
            "message": f"Your skin health has {trend} by {abs(diff)} points since your last scan.",
        }

    # ==============================================
    # 6. RETURN
    # ==============================================
    return {
        "recommendations": unique_recs,
        "progress_summary": progress,
        "overall_health_score": scan_result.get("overall_health_score"),
        "skin_type": skin_type,
    }
