FROM python:3.13-slim
WORKDIR /app
# Install minimal system dependencies for Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY server.py ./
RUN pip install --no-cache-dir \
    fastapi uvicorn psycopg2-binary \
    playwright beautifulsoup4 requests && \
    playwright install chromium
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
