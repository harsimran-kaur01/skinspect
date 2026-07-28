import torch
from pathlib import Path

model_path = Path("ml/models/acne_model.pth")
data = torch.load(model_path, map_location="cpu")

print(f"Type of loaded object: {type(data)}")
print(f"Content: {data}")

if isinstance(data, dict):
    print(f"\nKeys: {list(data.keys())}")
    for key, value in data.items():
        if isinstance(value, torch.Tensor):
            print(f"  {key} -> shape: {value.shape}")
        else:
            print(f"  {key} -> {type(value)}: {value}")
else:
    print("Not a dict – it's a single value or another object.")
    print(f"Value: {data}")
