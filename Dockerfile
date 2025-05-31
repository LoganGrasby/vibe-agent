# Use Ubuntu 22.04 as base image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Update package list and install Python and pip
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create a symbolic link for python command
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Install Python dependencies first for better caching
# Install google-adk-agents and other potential dependencies
RUN pip3 install --no-cache-dir google-adk

# Copy all files including .env
COPY . .

# Make sure the script is executable
RUN chmod +x code-agent/loop.py

# Expose any ports if needed (adjust as necessary)
EXPOSE 8000

# Set the entrypoint to run loop.py
ENTRYPOINT ["python3", "code-agent/loop.py"]