FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI and system-level build dependencies (libgomp for onnxruntime)
RUN apt-get update && apt-get install -y docker.io libgomp1 curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY execution_server.py .
COPY container_manager.py .

# Create directory for code execution (if needed locally, though we use sibling containers)
RUN mkdir -p /code

EXPOSE 5051

CMD ["python", "execution_server.py"]
