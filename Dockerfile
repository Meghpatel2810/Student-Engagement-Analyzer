FROM python:3.10-slim

# Install system dependencies needed for OpenCV/Ultralytics
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (Required for Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory
WORKDIR $HOME/app

# Copy requirements and install
# We assume the Docker build context is the root of your project
COPY --chown=user backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code and necessary shared folders
COPY --chown=user backend/ ./backend/
COPY --chown=user models/ ./models/
COPY --chown=user common/ ./common/

# Set working directory to backend so main.py is in scope
WORKDIR $HOME/app/backend

# Expose port 7860, which is what Hugging Face Spaces expects
EXPOSE 7860

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
