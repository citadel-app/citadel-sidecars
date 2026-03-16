import json
import numpy as np

try:
    with open("voices.json", "r") as f:
        voices = json.load(f)
    
    print(f"Loaded {len(voices)} voices from voices.json")
    
    # helper to convert list to array
    voices_arrays = {k: np.array(v, dtype=np.float32) for k, v in voices.items()}
    
    np.savez("voices.npz", **voices_arrays)
    print("Saved voices.npz")
    
    # Verify
    loaded = np.load("voices.npz")
    print(f"Verified load: {len(loaded.files)} voices")
    
except Exception as e:
    print(f"Error converting: {e}")
