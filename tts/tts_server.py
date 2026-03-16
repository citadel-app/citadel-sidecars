import io
import os
import hashlib
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from kokoro_onnx import Kokoro

app = FastAPI(title="Codex Local TTS Server")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Kokoro
# We expect model.onnx and voices.json to be in the same directory as this script
# OR in a mounted /app/models directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOUNTED_MODELS_DIR = "/app/models"

def get_model_path():
    # Priority: 1. Mounted volume, 2. Script directory
    mounted_path = os.path.join(MOUNTED_MODELS_DIR, "kokoro-v0_19.onnx")
    if os.path.exists(mounted_path):
        return mounted_path
    return os.path.join(SCRIPT_DIR, "kokoro-v0_19.onnx")

def get_voices_path():
    # Priority: 1. voices.npz in mounted, 2. voices.json in mounted, 3. local voices.npz
    npz_mounted = os.path.join(MOUNTED_MODELS_DIR, "voices.npz")
    if os.path.exists(npz_mounted):
        return npz_mounted
    
    json_mounted = os.path.join(MOUNTED_MODELS_DIR, "voices.json")
    if os.path.exists(json_mounted):
        return json_mounted
        
    return os.path.join(SCRIPT_DIR, "voices.npz")

MODEL_PATH = get_model_path()
VOICES_PATH = get_voices_path()

# Disk cache directory
CACHE_DIR = os.getenv("TTS_CACHE_DIR", os.path.join(SCRIPT_DIR, ".tts_cache"))
os.makedirs(CACHE_DIR, exist_ok=True)


kokoro = None

def load_model():
    global kokoro
    if os.path.exists(MODEL_PATH) and os.path.exists(VOICES_PATH):
        print(f"Loading Kokoro model from {MODEL_PATH}...")
        try:
            kokoro = Kokoro(MODEL_PATH, VOICES_PATH)
            print("Kokoro model loaded successfully.")
        except Exception as e:
            print(f"Failed to load Kokoro model: {e}")
    else:
        print(f"WARNING: Model files not found at {MODEL_PATH}. Please run download_model.py")

# Try loading on startup
load_model()

def _cache_key(text: str, voice: str, speed: float) -> str:
    """Generate a deterministic cache key from request parameters."""
    raw = f"{text}|{voice}|{speed:.2f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _get_cached(key: str) -> bytes | None:
    """Return cached WAV bytes if they exist, else None."""
    path = os.path.join(CACHE_DIR, f"{key}.wav")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None

def _put_cache(key: str, wav_bytes: bytes) -> None:
    """Write WAV bytes to disk cache."""
    path = os.path.join(CACHE_DIR, f"{key}.wav")
    with open(path, "wb") as f:
        f.write(wav_bytes)

class TtsRequest(BaseModel):
    text: str
    voice: str = "af_sarah" # Default voice
    speed: float = 1.0

@app.get("/status")
def get_status():
    cache_files = len(os.listdir(CACHE_DIR)) if os.path.isdir(CACHE_DIR) else 0
    return {
        "status": "ok", 
        "model_loaded": kokoro is not None,
        "model_path": MODEL_PATH,
        "cache_entries": cache_files
    }

@app.get("/voices")
def get_voices():
    # Helper to return common voices since kokoro-onnx doesn't expose them directly easily
    return [
        {"id": "af_sarah", "name": "Sarah (Female)"},
        {"id": "af_bella", "name": "Bella (Female)"},
        {"id": "af_nicole", "name": "Nicole (Female)"},
        {"id": "af_sky",   "name": "Sky (Female)"},
        {"id": "am_adam",  "name": "Adam (Male)"},
        {"id": "am_michael", "name": "Michael (Male)"}
    ]

@app.delete("/cache")
def clear_cache():
    """Clear the TTS audio cache."""
    count = 0
    for f in os.listdir(CACHE_DIR):
        if f.endswith(".wav"):
            os.remove(os.path.join(CACHE_DIR, f))
            count += 1
    return {"cleared": count}

@app.post("/tts")
async def generate_tts(request: TtsRequest):
    global kokoro
    if kokoro is None:
        # Try loading again just in case files were dropped in
        load_model()
        if kokoro is None:
            raise HTTPException(status_code=503, detail="Model not loaded. Please run download_model.py on the server.")
    
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Check cache first
    key = _cache_key(request.text.strip(), request.voice, request.speed)
    cached = _get_cached(key)
    if cached is not None:
        print(f"Cache HIT for: '{request.text[:30]}...'")
        return Response(content=cached, media_type="audio/wav")

    try:
        # Generate audio
        # kokoro.create returns (audio_samples, sample_rate)
        print(f"Cache MISS — generating TTS for: '{request.text[:30]}...' with voice {request.voice}")
        samples, sample_rate = kokoro.create(
            request.text, 
            voice=request.voice, 
            speed=request.speed, 
            lang="en-us"
        )
        
        # Convert to WAV in-memory (PCM_16 for browser compatibility)
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, samples, sample_rate, format='WAV', subtype='PCM_16')
            wav_content = wav_buffer.getvalue()

        # Store in cache
        _put_cache(key, wav_content)
            
        return Response(content=wav_content, media_type="audio/wav")
    except Exception as e:
        print(f"Error generating TTS: {e}")
        # If it's a voice error, give a specific message
        if "voice" in str(e).lower():
             raise HTTPException(status_code=400, detail=f"Voice generation failed. Voice '{request.voice}' might be invalid. Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("TTS_PORT", "5050"))
    print(f"Starting TTS Server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
