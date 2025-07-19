# Use Microsoft Playwright Ubuntu image (arm64) - this has all Playwright browsers pre-installed
FROM mcr.microsoft.com/playwright:v1.46.0-jammy-arm64

# Switch to root to install packages
USER root

# 1️⃣ Node – update to supported version and install n8n
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g n8n

# 2️⃣ Python – Nova Act + Playwright
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir nova-act requests && \
    python3 -m playwright install --with-deps

# 3️⃣ Copy custom node & runner
COPY python/nova_runner.py /opt/nova_runner.py

# 4️⃣ Create a non-root user for n8n first
RUN useradd -m -s /bin/bash node

# 5️⃣ Create the correct directory structure for n8n (single .n8n, not nested)
RUN mkdir -p /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act && \
    chown -R node:node /home/node/.n8n

# Copy node files to correct location  
COPY --chown=node:node package.json /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/
COPY --chown=node:node dist/src/ /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/src/
COPY --chown=node:node dist/nodes/ /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/nodes/

# Fix package.json paths to match deployed structure
RUN sed -i 's|"dist/src/|"src/|g' /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/package.json && \
    sed -i 's|"dist/nodes/|"nodes/|g' /home/node/.n8n/nodes/n8n-nodes-amazon-nova-act/package.json

# Install the node package properly as node user
USER node
RUN cd /home/node/.n8n/nodes && \
    echo '{"name":"installed-nodes","private":true,"dependencies":{"n8n-nodes-amazon-nova-act":"file:./n8n-nodes-amazon-nova-act"}}' > package.json && \
    npm install

# Switch back to root briefly for final setup
USER root

# 6️⃣ Set up environment
ENV NOVA_ACT_API_KEY=__replace_me__
ENV NOVA_RUNNER=/opt/nova_runner.py
ENV NOVA_ACT_SKIP_PLAYWRIGHT_INSTALL=1

# Switch to node user
USER node
WORKDIR /home/node

# Expose n8n port
EXPOSE 5678

# Start n8n with full path
CMD ["/usr/bin/n8n"]