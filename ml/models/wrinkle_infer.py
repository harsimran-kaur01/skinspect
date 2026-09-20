import torch
import torch.nn as nn
import segmentation_models_pytorch as smp
from pathlib import Path
import numpy as np
from PIL import Image
import torchvision.transforms as transforms


class WrinkleSegmentationModel(nn.Module):
    """U-Net with EfficientNet-B4 encoder for wrinkle segmentation."""

    def __init__(self):
        super().__init__()
        self.model = smp.Unet(
            encoder_name="efficientnet-b4",
            encoder_weights=None,  # we'll load from checkpoint
            in_channels=3,
            classes=1,
            activation=None,
            decoder_attention_type="scse",
        )

    def forward(self, x):
        return self.model(x)


class WrinkleInfer:
    def __init__(self, config):
        self.config = config
        base_dir = Path(__file__).resolve().parents[1]
        model_filename = config.get("model_path", "models/wrinkle_model.pth")
        self.model_path = base_dir / model_filename

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.input_size = config.get("input_size", 256)
        self.confidence_threshold = config.get("confidence_threshold", 0.5)

        self.model = self._load_model()
        self.transform = self._get_transform()

    def _strip_model_prefix(self, state_dict):
        """Remove 'model.' prefix from keys if present."""
        new_state_dict = {}
        for key, value in state_dict.items():
            new_key = key[6:] if key.startswith("model.") else key
            new_state_dict[new_key] = value
        return new_state_dict

    def _load_model(self):
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        model = WrinkleSegmentationModel()
        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)

        if isinstance(checkpoint, dict):
            if "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]
            elif "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                state_dict = checkpoint
        else:
            state_dict = checkpoint

        state_dict = self._strip_model_prefix(state_dict)

        try:
            model.model.load_state_dict(state_dict)
        except RuntimeError as e:
            print(f"⚠️ Error loading state_dict: {e}")
            print("   Keys in state_dict:", list(state_dict.keys())[:5])
            print("   Keys in model:", list(model.model.state_dict().keys())[:5])
            raise

        model.to(self.device)
        model.eval()
        print(f"✅ Wrinkle model loaded from {self.model_path}")
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
              confidence: mean predicted probability over the segmented mask
              severity: "none" | "mild" | "moderate" | "severe"
              area_pct: percentage of face area classified as wrinkled
              detected: bool — whether wrinkles were confidently detected
        """
        img = Image.fromarray((preprocessed_image * 255).astype(np.uint8))
        input_tensor = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(input_tensor)  # shape: (1, 1, H, W)
            probs = torch.sigmoid(logits)  # (1, 1, H, W)

        mask = probs > 0.5
        area_pct = mask.float().mean().item() * 100
        confidence = probs[mask].mean().item() if mask.any() else 0.0

        if area_pct < 5:
            severity = "none"
        elif area_pct < 15:
            severity = "mild"
        elif area_pct < 35:
            severity = "moderate"
        else:
            severity = "severe"

        # Same fix as acne_infer.py: no more confidence-flipping. A
        # low-confidence result now cleanly resolves to "not detected"
        # instead of producing a contradictory high confidence value.
        detected = severity != "none" and confidence >= self.confidence_threshold

        if not detected:
            severity = "none"
            area_pct = 0

        return {
            "confidence": round(confidence, 3),
            "severity": severity,
            "area_pct": int(area_pct),
            "detected": detected,
        }
