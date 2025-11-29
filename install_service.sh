#!/bin/bash
# ATLAS v2.0 - Background Service Installer

echo "============================================================"
echo "🛡️  ATLAS v2.0 - Background Service Installer"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script needs sudo privileges."
    echo "Running with sudo..."
    sudo "$0" "$@"
    exit $?
fi

SCRIPT_DIR="/root/telbot"
SERVICE_FILE="$SCRIPT_DIR/atlas.service"
SYSTEMD_DIR="/etc/systemd/system"

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Error: atlas.service not found in $SCRIPT_DIR"
    exit 1
fi

# Check if .env exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create .env with your API credentials before starting the service."
    echo ""
fi

echo "📋 Installation Steps:"
echo ""

# Step 1: Copy service file
echo "1. Copying service file to systemd..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/atlas.service"
if [ $? -eq 0 ]; then
    echo "   ✅ Service file copied"
else
    echo "   ❌ Failed to copy service file"
    exit 1
fi

# Step 2: Reload systemd
echo "2. Reloading systemd daemon..."
systemctl daemon-reload
if [ $? -eq 0 ]; then
    echo "   ✅ Systemd reloaded"
else
    echo "   ❌ Failed to reload systemd"
    exit 1
fi

# Step 3: Enable service
echo "3. Enabling ATLAS to start on boot..."
systemctl enable atlas
if [ $? -eq 0 ]; then
    echo "   ✅ Auto-start enabled"
else
    echo "   ❌ Failed to enable auto-start"
    exit 1
fi

# Step 4: Start service
echo "4. Starting ATLAS service..."
systemctl start atlas
sleep 2

# Step 5: Check status
echo "5. Checking service status..."
if systemctl is-active --quiet atlas; then
    echo "   ✅ ATLAS is running!"
else
    echo "   ⚠️  ATLAS may not be running properly"
    echo ""
    echo "Check status with: sudo systemctl status atlas"
    echo "Check logs with: sudo journalctl -u atlas -f"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ ATLAS v2.0 Successfully Installed as Background Service!"
echo "============================================================"
echo ""
echo "📊 Service Status:"
systemctl status atlas --no-pager -l | head -n 10
echo ""
echo "📚 Useful Commands:"
echo ""
echo "  View live logs:      sudo journalctl -u atlas -f"
echo "  Check status:        sudo systemctl status atlas"
echo "  Restart service:     sudo systemctl restart atlas"
echo "  Stop service:        sudo systemctl stop atlas"
echo "  Disable auto-start:  sudo systemctl disable atlas"
echo ""
echo "🎯 Usage:"
echo "  1. Open Telegram"
echo "  2. Go to 'Saved Messages'"
echo "  3. Send: .atlas @channel 100"
echo ""
echo "💡 View logs in real-time:"
echo "  sudo journalctl -u atlas -f"
echo ""
echo "============================================================"
