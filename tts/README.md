# Citadel Text-to-Speech (TTS) Sidecar

This service utilizes the `kokoro-onnx` model to run an offline, local Text-to-Speech engine. It exposes a FastAPI server designed to quickly synthesize text into spoken audio files.

## Running the Container

This container is designed to be pulled and managed by the main Citadel Electron app, but you can run it manually:

```bash
docker run -p 5050:5050 ghcr.io/citadel-app/sidecar-tts:latest
```

## Internal Files

When shelling into this container, you will find:
*   `tts_server.py`: The FastAPI server application.
*   `voices.npz` & `voices.json`: The ONNX model voice data files.
*   `README.md`: This file.
*   `ROOT_README.md`: The repository overview README.
