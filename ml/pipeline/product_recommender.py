"""
Product recommendation engine based on:
- Acne severity
- Wrinkle severity
- Skin type (from questionnaire)
"""


class ProductRecommender:
    def __init__(self):
        self.product_db = self._init_product_db()

    def _init_product_db(self):
        return {
            "acne": {
                "mild": [
                    {
                        "name": "Salicylic Acid Cleanser",
                        "type": "cleanser",
                        "description": "Gentle daily cleanser to unclog pores",
                    },
                    {
                        "name": "Tea Tree Oil Serum",
                        "type": "serum",
                        "description": "Natural anti-inflammatory for mild acne",
                    },
                ],
                "moderate": [
                    {
                        "name": "Benzoyl Peroxide Gel",
                        "type": "treatment",
                        "description": "Targeted treatment for active breakouts",
                    },
                    {
                        "name": "Niacinamide Serum",
                        "type": "serum",
                        "description": "Reduces inflammation and redness",
                    },
                ],
                "severe": [
                    {
                        "name": "Adapalene Gel",
                        "type": "prescription",
                        "description": "Retinoid for severe acne - consult dermatologist",
                    },
                    {
                        "name": "Azelaic Acid Cream",
                        "type": "prescription",
                        "description": "For inflammatory acne and hyperpigmentation",
                    },
                ],
            },
            "wrinkles": {
                "mild": [
                    {
                        "name": "Hyaluronic Acid Serum",
                        "type": "serum",
                        "description": "Hydrates and plumps fine lines",
                    },
                    {
                        "name": "Vitamin C Serum",
                        "type": "serum",
                        "description": "Antioxidant protection for aging skin",
                    },
                ],
                "moderate": [
                    {
                        "name": "Retinol Cream",
                        "type": "treatment",
                        "description": "Stimulates collagen production",
                    },
                    {
                        "name": "Peptide Cream",
                        "type": "moisturizer",
                        "description": "Supports skin firmness and elasticity",
                    },
                ],
                "severe": [
                    {
                        "name": "Prescription Retinoid",
                        "type": "prescription",
                        "description": "Consult dermatologist for Tretinoin",
                    },
                    {
                        "name": "Growth Factor Serum",
                        "type": "treatment",
                        "description": "Advanced anti-aging treatment",
                    },
                ],
            },
        }

    def recommend(self, acne_severity, wrinkle_severity, skin_type):
        recommendations = []

        # Acne recommendations
        if acne_severity in self.product_db["acne"]:
            for product in self.product_db["acne"][acne_severity]:
                product["category"] = "acne_treatment"
                recommendations.append(product)

        # Wrinkle recommendations
        if wrinkle_severity in self.product_db["wrinkles"]:
            for product in self.product_db["wrinkles"][wrinkle_severity]:
                product["category"] = "anti_aging"
                recommendations.append(product)

        # Add skin-type specific recommendations
        skin_type_products = self._get_skin_type_products(skin_type)
        recommendations.extend(skin_type_products)

        # Limit to top 5 recommendations
        return recommendations[:5]

    def _get_skin_type_products(self, skin_type):
        """Products specific to skin type"""
        products = {
            "dry": [
                {
                    "name": "Ceramide Moisturizer",
                    "type": "moisturizer",
                    "description": "Restores skin barrier and hydration",
                }
            ],
            "oily": [
                {
                    "name": "Oil-Free Moisturizer",
                    "type": "moisturizer",
                    "description": "Hydrates without clogging pores",
                }
            ],
            "combination": [
                {
                    "name": "Balancing Moisturizer",
                    "type": "moisturizer",
                    "description": "Hydrates dry areas while controlling oil",
                }
            ],
            "sensitive": [
                {
                    "name": "Fragrance-Free Moisturizer",
                    "type": "moisturizer",
                    "description": "Gentle formula for sensitive skin",
                }
            ],
            "normal": [
                {
                    "name": "Daily SPF Moisturizer",
                    "type": "moisturizer",
                    "description": "Hydration with sun protection",
                }
            ],
        }

        return products.get(skin_type, [])
