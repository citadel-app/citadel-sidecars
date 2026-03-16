# Citadel Execution Sidecar

This service utilizes Docker-in-Docker functionality to execute arbitrary code in isolated sandbox environments. It exposes a Flask server used by the Citadel Electron application to interact with these sandboxes.

## Expected Environment

This container requires access to a Docker daemon. It is intended to build and manage its own sibling containers (which do the actual running), making it essentially a control plane. In production, Citadel handles binding the Docker socket internally. 

```bash
docker run -v /var/run/docker.sock:/var/run/docker.sock -p 5051:5051 ghcr.io/citadel-app/sidecar-execution:latest
```

## Internal Files

When shelling into this container, you will find:
*   `execution_server.py`: The Flask API control server.
*   `container_manager.py`: The wrapper module managing the sibling Docker containers.
*   `README.md`: This file.
*   `ROOT_README.md`: The repository overview README.
