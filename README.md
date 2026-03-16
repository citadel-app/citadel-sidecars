# Citadel Sidecars

This repository contains the sidecar processes used by the Citadel AI Desktop Application. These are containerized microservices that provide specific offline AI capabilities to the main Electron application.

## Overview

Citadel is designed to run its AI features entirely locally. To achieve this in a cross-platform and modular way, the heavier workloads (like Text-to-Speech and Code Execution) are decoupled from the main Electron app and run as separate Docker containers — these are the "sidecars".

## Components

The repository is divided into two primary sidecar services:

*   **[`/tts`](./tts/README.md)**: A Text-to-Speech engine utilizing the Kokoro ONNX model for high-quality, offline voice generation.
*   **[`/execution`](./execution/README.md)**: A secure, sandboxed code execution environment utilizing Docker and Flask to run AI-generated code safely.

## Usage

These sidecars are designed to be spun up and managed automatically by the main Citadel Electron application. However, you can also build and run them independently for testing or development. See the respective READMEs in their folders for instructions on how to build and run each sidecar manually.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
