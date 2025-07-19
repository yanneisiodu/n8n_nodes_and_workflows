#!/bin/bash

echo "Testing Amazon Nova Act n8n Node"
echo "================================="

# Check if Python script exists
if [ -f "dist/nodes/NovaAct/nova_act_runner.py" ]; then
    echo "✅ Python script found"
else
    echo "❌ Python script not found"
    exit 1
fi

# Check if TypeScript files were built
if [ -f "dist/src/nodes/NovaAct/NovaAct.node.js" ]; then
    echo "✅ Node.js file built successfully"
else
    echo "❌ Node.js file not found"
    exit 1
fi

# Check if credentials file exists
if [ -f "dist/src/credentials/NovaActApi.credentials.js" ]; then
    echo "✅ Credentials file built successfully"
else
    echo "❌ Credentials file not found"
    exit 1
fi

# Check if icon exists
if [ -f "dist/nodes/NovaAct/novaAct.svg" ]; then
    echo "✅ Icon file copied successfully"
else
    echo "❌ Icon file not found"
    exit 1
fi

echo ""
echo "✅ Build verification completed successfully!"
echo ""
echo "Next steps:"
echo "1. Get your Nova Act API key from https://nova.amazon.com/act"
echo "2. Build and run with Docker: docker-compose up --build -d"
echo "3. Access n8n at http://localhost:5678 (admin/password)"
echo "4. Add your Nova Act credentials in n8n"
echo "5. Create a workflow with the Amazon Nova Act node"
echo ""
echo "For development:"
echo "- Run: npm link"
echo "- In your n8n directory: npm link n8n-nodes-amazon-nova-act"
echo "- Restart n8n to see the new node"