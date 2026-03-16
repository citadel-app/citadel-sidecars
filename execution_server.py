from flask import Flask, request, jsonify
from flask_cors import CORS
import docker
import os
import tempfile
import time
from container_manager import ContainerManager

app = Flask(__name__)
CORS(app)

import signal
import sys
import atexit

container_manager = ContainerManager()

def shutdown_handler(signum=None, frame=None):
    print(f"[ExecutionServer] Shutdown signal received ({signum}). Cleaning up...")
    container_manager.purge_pool()
    sys.exit(0)

# Register handlers
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)
atexit.register(container_manager.purge_pool)

# Start warming up on server start
container_manager.warm_up_pools()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "execution-server"})


@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.json
    code = data.get('code')
    image = data.get('image', 'python:3.9-slim')
    command_template = data.get('command', 'python /code/script.py')
    stdin = data.get('stdin', '')
    
    if not code:
        return jsonify({"error": "No code provided"}), 400

    print(f"[DEBUG] Received execution request for image: {image}")
    print(f"[DEBUG] Provided extension: {data.get('extension')}")

    start_time = time.time()
    container = None
    is_warm = False
    
    try:
        # Determine extension and filename
        extension = data.get('extension', 'txt')
        if 'extension' not in data and '.' in command_template:
            # legacy fallback
            extension = command_template.split('.')[-1]
        
        filename = f"script.{extension}"
        print(f"[DEBUG] Using filename: {filename}")

        # 1. Get Container
        container, is_warm = container_manager.get_container(image)

        # 2. Prepare Code in Container
        container.exec_run("mkdir -p /code")
        
        # Write Code File
        import io
        import tarfile
        
        pw_tar = io.BytesIO()
        with tarfile.open(fileobj=pw_tar, mode='w') as tar:
            data_bytes = code.encode('utf-8')
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(data_bytes)
            tar.addfile(tarinfo, io.BytesIO(data_bytes))
        pw_tar.seek(0)
        
        container.put_archive('/code', pw_tar)

        # Write Stdin File (if needed)
        if stdin:
            stdin_tar = io.BytesIO()
            with tarfile.open(fileobj=stdin_tar, mode='w') as tar:
                data_bytes = stdin.encode('utf-8')
                tarinfo = tarfile.TarInfo(name='input.txt')
                tarinfo.size = len(data_bytes)
                tar.addfile(tarinfo, io.BytesIO(data_bytes))
            stdin_tar.seek(0)
            container.put_archive('/code', stdin_tar)

        # 3. Execution Logic
        cmd = command_template
        if stdin:
             cmd = f"{cmd} < /code/input.txt"

        # Write run.sh
        run_script = io.BytesIO()
        with tarfile.open(fileobj=run_script, mode='w') as tar:
            script_content = f"cd /code\n{cmd}".encode('utf-8')
            tarinfo = tarfile.TarInfo(name='run.sh')
            tarinfo.size = len(script_content)
            tarinfo.mode = 0o755 # Make executable
            tar.addfile(tarinfo, io.BytesIO(script_content))
        run_script.seek(0)
        container.put_archive('/code', run_script)

        # 3. Execution Logic
        # Run the script via /bin/sh
        exec_cmd = ['/bin/sh', '/code/run.sh']

        exec_result = container.exec_run(
            exec_cmd,
            demux=True,
            workdir='/code'
        )
        
        stdout = exec_result.output[0].decode('utf-8') if exec_result.output and exec_result.output[0] else ''
        stderr = exec_result.output[1].decode('utf-8') if exec_result.output and exec_result.output[1] else ''
        exit_code = exec_result.exit_code

        duration = time.time() - start_time

        return jsonify({
            "stdout": stdout,
            "stderr": stderr,
            "exitCode": exit_code,
            "duration": duration,
            "isWarm": is_warm
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if container:
            container_manager.cleanup(container, is_warm)

if __name__ == '__main__':
    print("Starting Execution Server on port 5051...")
    # Threaded=True to handle multiple requests
    app.run(host='0.0.0.0', port=5051, threaded=True)
