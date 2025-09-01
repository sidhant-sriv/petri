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

# Copy the agent source code
COPY . /app/agent/

# Set Python path to include the agent module
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose Jupyter port
EXPOSE 8888

# Command to run Jupyter for development/prototyping
CMD ["sh", "-c", "jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=\"${JUPYTER_TOKEN:-petri_jupyter_token}\""]
