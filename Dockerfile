# ---------- BUILDER STAGE ----------
FROM python:3.11-slim AS builder

# Install build tools for Python deps that require compiling
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies into user environment
RUN pip install --user --no-cache-dir -r requirements.txt


# ---------- RUNTIME STAGE ----------
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy app source code
COPY . .

# Ensure PATH can see user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Expose FastAPI port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
