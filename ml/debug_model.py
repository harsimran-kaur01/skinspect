# debug_model.py
import torch
from pathlib import Path

model_paths = ["ml/models/acne_model.pth", "ml/models/wrinkle_model.pth"]

for path in model_paths:
    p = Path(path)
    if not p.exists():
        print(f"❌ {p} does not exist.")
        continue
    print(f"\n🔍 Inspecting: {p}")
    data = torch.load(p, map_location="cpu")
    print(f"Type: {type(data)}")
    if isinstance(data, dict):
        print("Keys:", list(data.keys()))
        # Check if it's state_dict or something else
        if "state_dict" in data:
            print("It's a checkpoint with 'state_dict' key.")
        elif all(isinstance(k, str) for k in data.keys()):
            print("Looks like a state_dict (keys are parameter names).")
        else:
            print("Unknown dict structure.")
    else:
        # Could be full model
        print(f"Object: {data}")
        print(f"Type: {type(data)}")
        if hasattr(data, "state_dict"):
            print("It's a torch.nn.Module (full model).")
