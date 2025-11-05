# Start from a base image with Python
FROM python:3.13-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file (we need to create this)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the producer script
COPY producer.py .

# Command to run when container starts
CMD ["python", "producer.py"]

## Build the Docker image
# docker build -t producer:v1 .

## Run the Docker container
# docker run producer:v1


# When I run docker-compose up OR docker-compose up producer, this happens:

# first, rebuild the image: docker-compose up --build producer

# 1 Docker Compose reads docker-compose.yml
# 2 Sees build: ./producer for the producer service
# 3 Looks in the ./producer directory for a Dockerfile
# 4 Builds an image from that Dockerfile (just like when I ran docker build manually)
# 5 Creates a container from that image
# 6 Runs the container in the same network as kafka, redis, etc.

# SO WE DON'T NEED TO RUN docker build AND docker run MANUALLY IF WE USE DOCKER-COMPOSE UP
