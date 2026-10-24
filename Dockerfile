# Multi-stage Dockerfile for Second Brain AI (Render.com / Cloud deployment)

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /build/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend with G++ Sandbox
FROM python:3.12-slim AS runner

WORKDIR /app

# Install system dependencies: g++ for C++ sandbox, curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy Backend application
COPY backend/ ./backend/

# Copy built frontend assets
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

# Create storage directories
RUN mkdir -p /app/data/uploads /app/data/backups /app/data/logs

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app/backend

EXPOSE 8000

WORKDIR /app/backend

# Render passes $PORT dynamically
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
