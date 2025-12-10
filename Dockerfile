# Carnatic Music Learning Platform v2.0 - Production Docker Image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and web server
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libsndfile1-dev \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-v2.txt .
# Use --prefer-binary to avoid compiling C extensions (important for arm64 emulation)
RUN pip install --no-cache-dir --prefer-binary -r requirements-v2.txt

# Copy application code structure
COPY app_v2.py .
COPY api/ ./api/
COPY core/ ./core/
COPY modules/ ./modules/
COPY config/ ./config/
COPY static/ ./static/
COPY templates/ ./templates/

# Create a non-root user for security
RUN groupadd -r carnatic && useradd -r -g carnatic -m carnatic
RUN chown -R carnatic:carnatic /app
USER carnatic

# Expose port for web interface
EXPOSE 5001

# Set environment variables
ENV FLASK_APP=app_v2.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check for v2.0 API
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/v1/health || exit 1

# Run the Flask application with SocketIO support
CMD ["python", "app_v2.py"]
