#!/bin/bash
set -e

echo "=== After Install Script ==="

cd /home/ec2-user/app

# Remove old venv if it exists (might be broken from previous deployment)
if [ -d "/home/ec2-user/app/.venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf /home/ec2-user/app/.venv
    echo "✅ Old venv removed"
fi

# Ensure correct ownership
chown -R ec2-user:ec2-user /home/ec2-user/app

# Install/update dependencies using UV as ec2-user
echo "Syncing dependencies with UV..."
su - ec2-user -c 'cd /home/ec2-user/app && /home/ec2-user/.local/bin/uv sync'
echo "✅ Dependencies synced"

# Create/update systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/streamlit.service <<'EOF'
[Unit]
Description=Streamlit Lounge Access Advisor
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/app
Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ec2-user/.local/bin/uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✅ Systemd service updated"

echo "=== After Install Complete ==="