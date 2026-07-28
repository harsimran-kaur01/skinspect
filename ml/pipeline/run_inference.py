#!/usr/bin/env python3
"""
Standalone inference pipeline for SkinSpect.
Takes an image, runs face detection + quality check + models,
outputs JSON matching Phase 0 contract.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import cv2
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.acne_infer import AcneInfer
from models.wrinkle_infer import WrinkleInfer
from pipeline.preprocess import detect_face, preprocess_image
from pipeline.photo_guidance import PhotoGuidance
from pipeline.product_recommender import ProductRecommender


class SkinSpectPipeline:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Initialize models
        self.acne_model = AcneInfer(self.config.get("acne", {}))
        self.wrinkle_model = WrinkleInfer(self.config.get("wrinkle", {}))

        # Initialize helpers
        self.photo_guide = PhotoGuidance()
        self.recommender = ProductRecommender()

    def run(self, image_path, questionnaire=None, save_crop=False):
        """
        Main inference pipeline.

        Args:
            image_path: Path to image
            questionnaire: Dict with skin_type, concerns, etc. from user
            save_crop: Save cropped face image
        """
        start_time = time.perf_counter()

        # 1. Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # 2. Photo quality check
        quality = self.photo_guide.analyze_image(img)
        if quality["quality_score"] < 60:
            return {
                "error": "Photo quality insufficient",
                "guidance": self.photo_guide.get_guidance_message(quality),
                "quality_score": quality["quality_score"],
            }

        # 3. Detect face and crop
        face_crop, bbox = detect_face(img)
        if face_crop is None:
            raise RuntimeError("No face detected in image")

        if save_crop:
            crop_path = Path(image_path).stem + "_crop.jpg"
            cv2.imwrite(str(crop_path), face_crop)
            print(f"📸 Saved crop: {crop_path}")

        # 4. Preprocess
        preprocessed = preprocess_image(face_crop, self.config.get("preprocess", {}))

        # 5. Run models
        acne_result = self.acne_model.predict(preprocessed)
        wrinkle_result = self.wrinkle_model.predict(preprocessed)

        # 6. Get skin type from questionnaire (or default)
        skin_type = (
            questionnaire.get("skin_type", "combination")
            if questionnaire
            else "combination"
        )

        # 7. Generate recommendations
        products = self.recommender.recommend(
            acne_severity=acne_result["severity"],
            wrinkle_severity=wrinkle_result["severity"],
            skin_type=skin_type,
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # 8. Build output
        output = self._build_output(
            image_path=image_path,
            acne=acne_result,
            wrinkle=wrinkle_result,
            skin_type=skin_type,
            products=products,
            quality_score=quality["quality_score"],
            processing_time_ms=elapsed_ms,
        )
        return output

    def _build_output(
        self,
        image_path,
        acne,
        wrinkle,
        skin_type,
        products,
        quality_score,
        processing_time_ms,
    ):
        from uuid import uuid4

        scan_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).isoformat() + "Z"

        # Build conditions list — use the explicit "detected" flag from
        # each model instead of re-comparing confidence against a
        # threshold a second time here (that duplicate check used to
        # produce contradictory "detected" conditions with severity="none").
        conditions = []

        if acne["detected"]:
            conditions.append(
                {
                    "condition": "acne",
                    "confidence": acne["confidence"],
                    "severity": acne["severity"],
                    "affected_area_percentage": acne["area_pct"],
                    "description": f"Acne detected with {acne['confidence']:.0%} confidence",
                }
            )

        if wrinkle["detected"]:
            conditions.append(
                {
                    "condition": "wrinkles",
                    "confidence": wrinkle["confidence"],
                    "severity": wrinkle["severity"],
                    "affected_area_percentage": wrinkle["area_pct"],
                    "description": f"Wrinkles detected with {wrinkle['confidence']:.0%} confidence",
                }
            )

        # Overall health score: this is a HEALTH score, so it should be
        # HIGH when conditions are absent/mild and LOW when conditions are
        # confidently detected as severe. Previously this averaged the
        # "problem confidence" directly, which meant confidently detected
        # severe acne produced a HIGHER "health" score than a clean face.
        #
        # severity_weight expresses how much each detected condition
        # should pull the score down, scaled by how confident the model is.
        severity_weight = {"mild": 0.25, "moderate": 0.55, "severe": 0.85}

        if conditions:
            penalty = sum(
                severity_weight.get(c["severity"], 0.5) * c["confidence"]
                for c in conditions
            ) / len(conditions)
            overall = int(round((1 - penalty) * 100))
        else:
            overall = 85  # no conditions confidently detected -> healthy default

        overall = max(0, min(100, overall))

        # Build recommendations for JSON
        recs = []
        for product in products:
            recs.append(
                {
                    "type": "product",
                    "title": product["name"],
                    "description": product["description"],
                    "priority": "high"
                    if product.get("type") == "prescription"
                    else "medium",
                    "category": product.get(
                        "category", product.get("type", "treatment")
                    ),
                }
            )

        output = {
            "scan_id": scan_id,
            "user_id": None,  # Will be filled by API
            "image_url": image_path,
            "thumbnail_url": None,
            "analysis_date": timestamp,
            "skin_conditions": conditions,
            "skin_type": skin_type,
            "overall_health_score": overall,
            "quality_score": quality_score,
            "recommendations": recs,
            "product_suggestions": products,  # Full product details
            "ai_model": {
                "model_name": "SkinSpect-v0.1",
                "model_version": "0.1.0",
                "processing_time_ms": processing_time_ms,
                "confidence_threshold": 0.5,
            },
            "follow_up_needed": overall < 60,
            "has_changes": False,
            "previous_scan_id": None,
        }
        return output


def main():
    parser = argparse.ArgumentParser(description="SkinSpect Inference Pipeline")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--output", help="Path to save JSON output")
    parser.add_argument("--save-crop", action="store_true", help="Save cropped face")
    parser.add_argument(
        "--skin-type",
        default="combination",
        choices=["dry", "oily", "combination", "normal", "sensitive"],
        help="Skin type from questionnaire",
    )
    parser.add_argument("--config", help="Path to config.yaml")
    args = parser.parse_args()

    questionnaire = {"skin_type": args.skin_type}

    pipeline = SkinSpectPipeline(args.config)
    result = pipeline.run(
        args.image, questionnaire=questionnaire, save_crop=args.save_crop
    )

    json_str = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(json_str)
        print(f"✅ Output saved to {args.output}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
