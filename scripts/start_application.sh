#!/bin/bash
set -e

echo "=== Starting Streamlit Application ==="

# Enable and start the service
systemctl enable streamlit
systemctl start streamlit

# Wait for service to start
sleep 5

# Check if service is running
if systemctl is-active --quiet streamlit; then
    echo "✅ Streamlit application started successfully"
    systemctl status streamlit --no-pager
else
    echo "❌ Failed to start Streamlit application"
    journalctl -u streamlit -n 50 --no-pager
    exit 1
fi

# Test if application is responding
if curl -f http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ Application is responding on port 8501"
else
    echo "⚠️  Application may still be starting up..."
fi

echo "=== Start Application Complete ==="