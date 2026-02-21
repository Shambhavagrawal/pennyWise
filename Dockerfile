# docker build -t blk-hacking-ind-shamb .

# ── Base OS Selection ────────────────────────────────────────────────────────
# python:3.12-slim is chosen because:
#   • Debian 12 (Bookworm) slim — minimal Linux attack surface
#   • Official Python image: reproducible, security-patched, OCI-compliant
#   • ~50 MB vs ~900 MB for full Debian — fast layer pull on judges' machines
#   • No unnecessary system packages; challenge logic is pure Python/FastAPI
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="shamb"
LABEL description="PennyWise — BlackRock Hacking India 2026 Challenge API"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install dependencies first (layer-cache friendly)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY backend/src ./src

# Create a non-root user for security
RUN useradd -m -u 1000 pennywise && chown -R pennywise:pennywise /app
USER pennywise

# Expose the challenge-required port
EXPOSE 5477

# Health check so judges can verify the service is live
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5477/health')" || exit 1

# Start the API on port 5477
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5477"]
