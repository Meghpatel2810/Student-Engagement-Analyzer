from fastapi import FastAPI

app = FastAPI(title="Student Engagement Analyzer API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Engagement Analyzer API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
