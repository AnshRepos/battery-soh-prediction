FROM artifactory-02.boschdevcloud.com/rbadas-public-registry-docker-remote/python:3.13-slim

LABEL version="0.3.2"

# Proxy settings as build arguments (not baked into final image)
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY=localhost,127.0.0.1,.bosch.com

WORKDIR /app

# Install uv via pip
RUN pip install uv

# Copy uv configuration and README required by hatchling at build time
COPY pyproject.toml uv.lock README.md ./

# Copy the server code
COPY etmmcpserver.py __init__.py ./
COPY core/ ./core/
COPY services/ ./services/
COPY tools/ ./tools/
COPY prompts/ ./prompts/

# Install dependencies
RUN uv sync --frozen --no-cache

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    HOME=/app

# Start ETM MCP server

# Create non-root user for security
RUN groupadd --system mcpuser && useradd --system --no-create-home --shell /bin/false --gid mcpuser mcpuser \
    && chown -R mcpuser:mcpuser /app
USER mcpuser

CMD ["uv", "run", "etmmcpserver.py"]
