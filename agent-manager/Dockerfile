# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including PostgreSQL dev headers
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the unified requirements file
COPY ../requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent-manager source code
COPY . /app/agent-manager/

# Copy the agent module (needed for worker processes)
COPY ../agent /app/agent/

# Set Python path to include both modules
ENV PYTHONPATH=/app:$PYTHONPATH

# Command to run the agent manager
CMD ["python", "agent-manager/main.py"]
