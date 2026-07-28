import json
from .recommendation_engine import generate_recommendations

# Mock scan_result
scan_result = {
    "skin_conditions": [
        {
            "condition": "acne",
            "confidence": 0.746,
            "severity": "mild",
            "affected_area_percentage": 15,
            "description": "Acne detected with 75% confidence",
        },
        {
            "condition": "wrinkles",
            "confidence": 0.735,
            "severity": "none",
            "affected_area_percentage": 0,
            "description": "Wrinkles detected with 74% confidence",
        },
    ],
    "skin_type": "combination",
    "overall_health_score": 74,
}

# Mock questionnaire
questionnaire = {
    "age": 25,
    "skin_type": "combination",
    "concerns": ["acne", "oiliness"],
    "sensitivity": False,
    "routine": {},
    "lifestyle_factors": {},
    "previous_scan": {"overall_health_score": 68},  # for progress
}

recommendations = generate_recommendations(scan_result, questionnaire)
print(json.dumps(recommendations, indent=2))
