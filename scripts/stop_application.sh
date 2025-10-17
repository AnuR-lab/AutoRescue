#!/bin/bash
set -e

echo "=== Stopping Streamlit Application ==="

# Stop the service if it's running
if systemctl is-active --quiet streamlit; then
    echo "Stopping Streamlit service..."
    systemctl stop streamlit
    echo "✅ Streamlit service stopped"
else
    echo "ℹ️  Streamlit service is not running"
fi

# Completely remove and recreate app directory
echo "Cleaning app directory for fresh deployment..."
if [ -d "/home/ec2-user/app" ]; then
    rm -rf /home/ec2-user/app
    echo "✅ App directory removed"
fi

# Recreate empty directory
mkdir -p /home/ec2-user/app
chown -R ec2-user:ec2-user /home/ec2-user/app
echo "✅ Fresh app directory created"

echo "=== Stop Application Complete ==="