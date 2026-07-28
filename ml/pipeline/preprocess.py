import cv2
import numpy as np

# Loaded once at import time instead of on every detect_face() call —
# reading and parsing the cascade XML from disk repeatedly was needless
# overhead on every single scan.
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def detect_face(image):
    """Detect largest face in image."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
    )
    if len(faces) == 0:
        return None, None
    (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
    face_crop = image[y : y + h, x : x + w]
    return face_crop, (x, y, w, h)


def preprocess_image(face_crop, config):
    """Resize and normalize face crop."""
    target_size = tuple(config.get("target_size", [224, 224]))
    rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, target_size)
    normalized = resized.astype(np.float32) / 255.0
    return normalized
