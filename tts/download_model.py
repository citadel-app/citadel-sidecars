import requests
import os

# URLs for the model and voices files (v0.19)
FILES = {
    "kokoro-v0_19.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx",
    "voices.json": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json"
}

def download_file(url, filename):
    if os.path.exists(filename):
        print(f"{filename} already exists. Skipping.")
        return
    
    print(f"Downloading {filename}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded {filename}")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")

if __name__ == "__main__":
    print("Setting up Kokoro-82M model files...")
    # Download in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    for filename, url in FILES.items():
        download_file(url, filename)
    
    print("\nSetup complete!")
    print("To run the server:")
    print("1. pip install -r requirements.txt")
    print("2. python download_model.py (you just ran this)")
    print("3. uvicorn tts_server:app --reload")
