FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for soundfile
RUN apt-get update && apt-get install -y libsndfile1 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code & small base assets
COPY tts_server.py .
COPY voices.npz .
COPY voices.json .
COPY README.md .
COPY ROOT_README.md .

EXPOSE 5050

CMD ["python", "tts_server.py"]
