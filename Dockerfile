# Hugging Face Spaces strictly requires a non-root user running on port 7860
FROM python:3.11-slim

# Install system dependencies for Playwright (if Tier 2 is triggered) and Node.js for Vite build
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up the non-root user 'user' with UID 1000 required by HF Spaces
RUN useradd -m -u 1000 user

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn

# Build the React Dashboard
COPY dashboard/ dashboard/
RUN cd dashboard && npm install && npm run build

# Copy the rest of the application
COPY --chown=user:user . /app/

# Switch to the non-root user
USER user

# Install playwright browsers (required by crawl4ai) in user space
RUN playwright install chromium

# Expose the mandatory Hugging Face port
EXPOSE 7860

# Run the unified app (Serves React on 7860 + starts Scraper daemon)
CMD ["python", "app.py"]
