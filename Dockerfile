# Go back to the working Alpine setup and add a fallback mechanism
FROM n8nio/n8n:latest

# Switch to root user to install packages
USER root

# --- KEY FIX: Tell Playwright to use the system's browser ---
# 1. This prevents pip from trying to download a browser during installation.
ENV PLAYWRIGHT_BROWSERS_PATH=0
# 2. This tells Playwright where to find the chromium executable we install via apk.
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser

# Update package list and install essential packages.
# Added nss, freetype, and harfbuzz which are common dependencies for Chromium.
RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    build-base \
    wget \
    ca-certificates \
    # Alpine's native Chromium and dependencies
    chromium \
    nss \
    freetype \
    harfbuzz \
    ttf-freefont \
    font-noto-emoji \
    && rm -rf /var/cache/apk/*

# Create a Python virtual environment
RUN python3 -m venv /opt/nova-act-venv

# Install Python packages into the virtual environment.
# Try to install playwright and nova-act with fallbacks
RUN /opt/nova-act-venv/bin/pip install --upgrade pip && \
    (/opt/nova-act-venv/bin/pip install playwright || echo "Playwright pip install failed, will use system chromium") && \
    /opt/nova-act-venv/bin/pip install nova-act

# Create symlinks so python3 points to the virtual environment
RUN ln -sf /opt/nova-act-venv/bin/python3 /usr/local/bin/python3 && \
    ln -sf /opt/nova-act-venv/bin/pip3 /usr/local/bin/pip3

# Create directory for Nova Act screenshots and logs, and set permissions
RUN mkdir -p /home/node/nova_logs /home/node/nova_screenshots /home/node/.n8n && \
    chown -R node:node /home/node/

# Set environment variables for Nova Act and n8n
# Ensure the venv is in the PATH
ENV PATH=/opt/nova-act-venv/bin:$PATH
ENV NOVA_ACT_LOGS_DIR=/home/node/nova_logs
ENV NOVA_ACT_SCREENSHOTS_DIR=/home/node/nova_screenshots
ENV N8N_USER_FOLDER=/home/node/.n8n

# Create the nodes directory (this is where the working version was)
RUN mkdir -p /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act && \
    chown -R node:node /home/node/.n8n/nodes

# Copy the node files directly to n8n's nodes directory with correct structure
COPY --chown=node:node package.json /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/
COPY --chown=node:node dist/src/ /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/src/
COPY --chown=node:node dist/nodes/ /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/nodes/

# Fix package.json paths to match the deployed structure (dist/src/ -> src/)
RUN sed -i 's|"dist/src/|"src/|g' /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/package.json && \
    sed -i 's|"dist/nodes/|"nodes/|g' /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/package.json

# Install the node using npm (this creates the package-lock.json and links it properly)
RUN cd /home/node/.n8n/nodes && \
    echo '{"name":"installed-nodes","private":true,"dependencies":{"n8n-nodes-amazon-nova-act":"file:./n8n-nodes-amazon-nova-act"}}' > package.json && \
    npm install

# Switch to the non-root node user for security
USER node

# Set working directory
WORKDIR /home/node

# Expose n8n port
EXPOSE 5678

# Simple verification
RUN python3 -c "print('🚀 Python environment ready')" && \
    ls -la /usr/bin/chromium-browser && \
    echo "✅ System Chromium available"

# Use the default n8n startup
# Don't override CMD, use the original from the base image