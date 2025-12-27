#!/bin/bash
# Install script for CAN bus stability fixes
# 
# This script installs:
# 1. Udev rule to set txqueuelen=1024 whenever can0 is created (including USB reconnects)
# 2. Udev rule to disable USB autosuspend for the CAN adapter
# 3. Systemd service as a backup
#
# Required to prevent "Timeout on wait for 'tmcuart_response'" errors during long prints

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=============================================="
echo "CAN Bus Stability Fix Installer"
echo "=============================================="
echo ""

# Install udev rules
echo "1. Installing udev rules..."

if [ -f "$SCRIPT_DIR/99-can-txqueuelen.rules" ]; then
    sudo cp "$SCRIPT_DIR/99-can-txqueuelen.rules" /etc/udev/rules.d/
    echo "   ✓ Installed 99-can-txqueuelen.rules"
else
    echo "   ⚠ Warning: 99-can-txqueuelen.rules not found"
fi

if [ -f "$SCRIPT_DIR/99-usb-can-no-autosuspend.rules" ]; then
    sudo cp "$SCRIPT_DIR/99-usb-can-no-autosuspend.rules" /etc/udev/rules.d/
    echo "   ✓ Installed 99-usb-can-no-autosuspend.rules"
else
    echo "   ⚠ Warning: 99-usb-can-no-autosuspend.rules not found"
fi

# Reload udev rules
echo ""
echo "2. Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "   ✓ Udev rules reloaded"

# Install systemd service as backup
echo ""
echo "3. Installing systemd service (backup)..."
if [ -f "$SCRIPT_DIR/can-txqueuelen.service" ]; then
    sudo cp "$SCRIPT_DIR/can-txqueuelen.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable can-txqueuelen.service
    sudo systemctl start can-txqueuelen.service 2>/dev/null || true
    echo "   ✓ Installed and enabled can-txqueuelen.service"
else
    echo "   ⚠ Warning: can-txqueuelen.service not found"
fi

# Apply fixes immediately
echo ""
echo "4. Applying fixes now..."
sudo ip link set can0 txqueuelen 1024 2>/dev/null || echo "   Note: can0 not available"
echo -1 | sudo tee /sys/bus/usb/devices/1-1/power/autosuspend > /dev/null 2>&1 || true
echo on | sudo tee /sys/bus/usb/devices/1-1/power/control > /dev/null 2>&1 || true
echo "   ✓ Applied immediate fixes"

# Verify
echo ""
echo "=============================================="
echo "Verification"
echo "=============================================="

CURRENT_TXQUEUELEN=$(cat /sys/class/net/can0/tx_queue_len 2>/dev/null || echo "N/A")
CURRENT_AUTOSUSPEND=$(cat /sys/bus/usb/devices/1-1/power/autosuspend 2>/dev/null || echo "N/A")

echo "CAN txqueuelen:    $CURRENT_TXQUEUELEN (should be 1024)"
echo "USB autosuspend:   $CURRENT_AUTOSUSPEND (should be -1)"
echo ""

if [ "$CURRENT_TXQUEUELEN" = "1024" ]; then
    echo "✓ SUCCESS: CAN txqueuelen correctly set to 1024"
else
    echo "⚠ WARNING: txqueuelen is $CURRENT_TXQUEUELEN"
fi

if [ "$CURRENT_AUTOSUSPEND" = "-1" ]; then
    echo "✓ SUCCESS: USB autosuspend disabled"
else
    echo "⚠ WARNING: USB autosuspend is $CURRENT_AUTOSUSPEND"
fi

echo ""
echo "=============================================="
echo "Installation complete!"
echo ""
echo "The udev rules will automatically apply fixes when:"
echo "- The system boots"
echo "- The USB CAN adapter reconnects"
echo "- can0 interface is created"
echo ""
echo "To verify after reboot:"
echo "  cat /sys/class/net/can0/tx_queue_len"
echo "  cat /sys/bus/usb/devices/1-1/power/autosuspend"
echo "=============================================="
