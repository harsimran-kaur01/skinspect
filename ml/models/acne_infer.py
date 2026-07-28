import torch
import torch.nn as nn
import torchvision.models as models
from pathlib import Path
import torchvision.transforms as transforms
import numpy as np
from PIL import Image


class AcneModel(nn.Module):
    """MobileNetV2 with custom head for 4-class acne grading."""

    def __init__(self, num_classes=4, dropout=0.3):
        super().__init__()
        base = models.mobilenet_v2(weights=None)
        self.features = base.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(
            nn.BatchNorm1d(1280),
            nn.Dropout(dropout),
            nn.Linear(1280, 256),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(256),
            nn.Dropout(0.15),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x)
        x = torch.flatten(x, 1)
        x = self.head(x)
        return x


class AcneInfer:
    def __init__(self, config):
        self.config = config
        base_dir = Path(__file__).resolve().parents[1]
        model_filename = config.get("model_path", "models/acne_model.pth")
        self.model_path = base_dir / model_filename

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_classes = config.get("num_classes", 4)
        self.dropout = config.get("dropout", 0.3)
        self.input_size = config.get("input_size", 224)
        self.confidence_threshold = config.get("confidence_threshold", 0.5)

        # IMPORTANT: This mapping MUST match the class_to_idx order used
        # during training (check your training ImageFolder/dataset object).
        # (severity, area_pct_estimate)
        self.class_map = {
            0: ("mild", 15),
            1: ("moderate", 35),
            2: ("severe", 60),
            3: ("none", 0),
        }

        self.model = self._load_model()
        self.transform = self._get_transform()

    def _load_model(self):
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        model = AcneModel(num_classes=self.num_classes, dropout=self.dropout)
        checkpoint = torch.load(self.model_path, map_location=self.device)

        if "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        elif "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
        else:
            state_dict = checkpoint

        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        print(f"✅ Acne model loaded from {self.model_path}")
        return model

    def _get_transform(self):
        return transforms.Compose(
            [
                transforms.Resize((self.input_size, self.input_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

    def predict(self, preprocessed_image):
        """
        preprocessed_image: numpy array (H,W,3) in [0,1]

        Returns:
            dict with:
              confidence: raw model confidence in its predicted class (0-1)
              severity: "none" | "mild" | "moderate" | "severe"
              area_pct: estimated affected area percentage
              detected: bool — whether acne was confidently detected
        """
        img = Image.fromarray((preprocessed_image * 255).astype(np.uint8))
        input_tensor = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(input_tensor)  # shape: (1, 4)
            probs = torch.softmax(logits, dim=1)  # shape: (1, 4)

        confidence, predicted_class = torch.max(probs, dim=1)
        confidence = confidence.item()
        predicted_class = predicted_class.item()

        severity, area_pct = self.class_map[predicted_class]

        # Only counts as "detected" if the model is both confident AND
        # predicted a non-"none" class. We no longer flip confidence
        # when below-threshold — that previously created contradictory
        # results downstream (e.g. severity="none" but confidence high
        # enough to still trigger the "condition detected" branch).
        detected = severity != "none" and confidence >= self.confidence_threshold

        if not detected:
            severity = "none"
            area_pct = 0

        return {
            "confidence": round(confidence, 3),
            "severity": severity,
            "area_pct": area_pct,
            "detected": detected,
        }
