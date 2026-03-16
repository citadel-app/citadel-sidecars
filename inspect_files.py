import sys

files = ["kokoro-v0_19.onnx", "voices.json"]

for f in files:
    try:
        with open(f, "rb") as fh:
            data = fh.read(100)
            print(f"File: {f}")
            print(f"Bytes: {data}")
            # Check for pickle proto 2-5
            if b'\x80\x02' in data or b'\x80\x03' in data or b'\x80\x04' in data: 
                print("DETECTED PICKLE!")
            if b'\x08\x03' in data: # Common ONNX start?
                 print("Possible Protobuf/ONNX start")
    except Exception as e:
        print(f"Error reading {f}: {e}")
