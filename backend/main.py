import sys
import os
import tempfile
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to sys.path so we can import from common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.pipeline import process_video

app = FastAPI(title="Student Engagement Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Engagement Analyzer API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    # Save the uploaded file to a temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
            tmp_in.write(await file.read())
            input_path = tmp_in.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
            output_path = tmp_out.name
            
        # Process video
        process_video(input_path, output_path)
        
        # Return the processed video file
        return FileResponse(output_path, media_type="video/mp4", filename=f"processed_{file.filename}")
        
    finally:
        pass # Optional cleanup could go here, but /tmp clears automatically and FileResponse needs the file open
