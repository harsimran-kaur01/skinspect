"""
Photo guidance and quality checks for skin analysis.
Helps users take better photos for accurate analysis.
"""

import cv2
import numpy as np
from skimage import exposure, filters
from skimage.metrics import structural_similarity as ssim


class PhotoGuidance:
    def __init__(self):
        self.min_brightness = 80
        self.max_brightness = 200
        self.min_face_size = 200  # pixels

    def analyze_image(self, image):
        """
        Analyze image quality and return feedback.
        Returns dict with: quality_score, issues, suggestions
        """
        results = {"quality_score": 0, "issues": [], "suggestions": []}

        # 1. Check brightness
        brightness = self._check_brightness(image)
        if brightness < self.min_brightness:
            results["issues"].append("Image too dark")
            results["suggestions"].append("Use better lighting")
        elif brightness > self.max_brightness:
            results["issues"].append("Image too bright/overexposed")
            results["suggestions"].append("Reduce lighting")
        else:
            results["quality_score"] += 20

        # 2. Check blur
        blur_score = self._check_blur(image)
        if blur_score < 30:
            results["issues"].append("Image is blurry")
            results["suggestions"].append("Hold camera steady")
        else:
            results["quality_score"] += 20

        # 3. Check face orientation
        orientation = self._check_face_orientation(image)
        if orientation == "not_detected":
            results["issues"].append("Face not clearly visible")
            results["suggestions"].append("Look directly at the camera")
        elif orientation == "side":
            results["issues"].append("Face is angled to the side")
            results["suggestions"].append("Face camera directly")
        else:
            results["quality_score"] += 20

        # 4. Check face size
        face_size = self._check_face_size(image)
        if face_size < self.min_face_size:
            results["issues"].append("Face is too small")
            results["suggestions"].append("Move closer to camera")
        else:
            results["quality_score"] += 20

        # 5. Check contrast
        contrast = self._check_contrast(image)
        if contrast < 0.3:
            results["issues"].append("Low contrast image")
            results["suggestions"].append("Improve lighting")
        else:
            results["quality_score"] += 20

        return results

    def _check_brightness(self, image):
        """Check average brightness"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return np.mean(gray)

    def _check_blur(self, image):
        """Check blur using Laplacian variance"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var

    def _check_face_orientation(self, image):
        """
        Check face orientation using MediaPipe or simple detection
        Returns: 'front', 'side', 'not_detected'
        """
        try:
            import mediapipe as mp

            mp_face_detection = mp.solutions.face_detection
            with mp_face_detection.FaceDetection(
                min_detection_confidence=0.5
            ) as face_detection:
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb)
                if not results.detections:
                    return "not_detected"

                # Check if both eyes are visible (indicates front-facing)
                # Simplified: check bounding box aspect ratio
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    h, w = image.shape[:2]
                    bbox_width = bbox.width * w
                    bbox_height = bbox.height * h
                    aspect = bbox_width / bbox_height

                    # Front face usually has aspect ratio close to 0.7-0.9
                    if 0.6 < aspect < 1.0:
                        return "front"
                    else:
                        return "side"
        except ImportError:
            # Fallback to OpenCV face detection
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, 1.1, 5)
            if len(faces) == 0:
                return "not_detected"
            return "front"

        return "front"

    def _check_face_size(self, image):
        """Check face size in pixels"""
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.1, 5)
        if len(faces) == 0:
            return 0
        # Return largest face size
        return max([w * h for (x, y, w, h) in faces])

    def _check_contrast(self, image):
        """Check image contrast"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return np.std(gray) / 128  # Normalized contrast

    def get_guidance_message(self, quality_results):
        """Generate user-friendly guidance message"""
        if quality_results["quality_score"] >= 80:
            return "✅ Great photo! Ready for analysis."

        msg = "📸 Photo tips:\n"
        for suggestion in quality_results["suggestions"]:
            msg += f"  • {suggestion}\n"

        if len(quality_results["issues"]) > 0:
            msg += "\n" + " ".join(quality_results["issues"])

        return msg
