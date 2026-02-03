# CVTeX Backend
FROM python:3.12-slim

# Install Tectonic (LaTeX compiler) and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    fontconfig \
    libfontconfig1 \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic
RUN curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh \
    && mv tectonic /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data output

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# Run the application
CMD ["python", "api.py"]
