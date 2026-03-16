import kokoro_onnx
import os
import inspect

print(f"Location: {os.path.dirname(kokoro_onnx.__file__)}")
try:
    print(inspect.getsource(kokoro_onnx.Kokoro))
except Exception as e:
    print(f"Could not get source: {e}")
