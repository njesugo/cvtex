# CVTeX Backend
FROM python:3.12-slim

# Install Tectonic (LaTeX compiler) and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    fontconfig \
    libfontconfig1 \
    libssl-dev \
    libgraphite2-3 \
    libharfbuzz0b \
    libicu72 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic from GitHub releases (pre-built binary)
RUN curl -L -o /tmp/tectonic.tar.gz https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz \
    && tar -xzf /tmp/tectonic.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/tectonic \
    && rm /tmp/tectonic.tar.gz \
    && tectonic --version

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
