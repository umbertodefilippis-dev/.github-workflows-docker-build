# Base image
FROM python:3.10-slim

# Create app user for security
RUN useradd -m appuser

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code into the image
COPY src/ ./src/

# Set ownership of /app to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
#USER appuser

# Set default environment variables (can be overridden with -e at runtime)
ENV INPUT_DIR=/data/input \
    OUTPUT_DIR=/data/output/ \
    LOG_DIR=/data/logs 

# Declare volumes (just informative – no effect at runtime unless used with `docker volume`)
#VOLUME ["/data/input", "/data/output/", "/data/logs", "/data/kernels"]

# Entrypoint
ENTRYPOINT ["python3", "src/raw2cal.py"]
CMD ["--input", "/data/input", "--output", "/data/output/", "--log", "/data/logs"]
