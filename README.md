# Student Engagement Analyzer

This project is a microservices-based web application for analyzing classroom videos to categorize student behavior into four engagement levels (E1-E4). It transitions a research pipeline (YOLO11 + ByteTrack + Transformer) into a production-ready application.

## Pipeline Details
- **Temporal Denoising:** 16-frame window.
- **Scoring:** 90-frame moving average.
- **Core Technologies:** YOLO11, ByteTrack, Transformer, Streamlit, FastAPI, Hugging Face Spaces.

## Architecture

The project is split into two main microservices:
1. **Frontend**: A Streamlit application providing the user interface for video upload and result visualization.
2. **Backend**: A FastAPI worker service that handles the heavy lifting of video processing and model inference.

## Directory Structure

- `frontend/`: Contains the Streamlit application code (`app.py`).
- `backend/`: Contains the FastAPI service code (`main.py`).
- `models/`: Directory for storing model weights (`.onnx`, `.pt`). Place weights here before deployment.
- `assets/`: Directory for sample videos, CSS, and images.
- `common/`: Shared utility scripts (e.g., scoring logic, helper functions).

## Deployment

### Backend Deployment (Hugging Face Spaces - Docker / FastAPI)
1. Set up a new Hugging Face Space.
2. Choose **Docker** as the SDK.
3. Ensure `packages.txt` is present to install system-level dependencies (`libGL`, `libglib`).
4. Set up a `Dockerfile` that runs the FastAPI app from the `backend/` directory using Uvicorn.
5. The API will be accessible via the Hugging Face Space URL.

### Frontend Deployment (Streamlit Cloud)
1. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Connect your GitHub repository containing this project.
3. Set the Main file path to `frontend/app.py`.
4. Add the Backend API URL to the Streamlit Cloud environment variables so the frontend can communicate with the Hugging Face backend.
