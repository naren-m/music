# Carnatic Music Learning Platform v2.0 - Production Docker Image
# Multi-architecture support: linux/amd64, linux/arm64
#
# Combined image: builds the React/Vite frontend, then serves it same-origin
# from the Flask backend (SPA_DIST_DIR) alongside the REST API and Socket.IO.

# ---- Stage 1: build the React frontend ----
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# build script is "vite build" (no tsc typecheck), so pre-existing type errors
# do not block the production bundle. Outputs /fe/dist.
RUN npm run build

# ---- Stage 2: Python backend serving the API + built SPA ----
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and web server
# Note: Package names are the same across amd64 and arm64
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    libsndfile1-dev \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
# Use --prefer-binary to avoid compiling C extensions (critical for arm64 cross-compilation)
# Using pip's binary preference ensures faster builds on both architectures
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code structure
COPY app.py .
COPY api/ ./api/
COPY core/ ./core/
COPY modules/ ./modules/
COPY config/ ./config/
COPY static/ ./static/
COPY templates/ ./templates/

# Copy the built SPA from the frontend stage and point Flask at it
COPY --from=frontend /fe/dist ./frontend_dist

# Create a non-root user for security
RUN groupadd -r carnatic && useradd -r -g carnatic -m carnatic
RUN chown -R carnatic:carnatic /app
USER carnatic

# Expose port for web interface
EXPOSE 5001

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV SPA_DIST_DIR=/app/frontend_dist
# App listens on PORT; keep it aligned with EXPOSE / k8s probes (5001)
ENV PORT=5001
# async_mode='threading' -> opt in to the threaded Werkzeug server in-container
ENV ALLOW_UNSAFE_WERKZEUG=1

# Health check for v2.0 API
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/v1/health || exit 1

# Run the Flask application with SocketIO support
CMD ["python", "app.py"]
