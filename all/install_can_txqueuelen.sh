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
if ip link show can0 > /dev/null 2>&1; then
    sudo ip link set can0 txqueuelen 1024
    echo "   ✓ Set can0 txqueuelen to 1024"
else
    echo "   Note: can0 interface not available; skipping immediate txqueuelen update"
fi

# Find and configure USB power settings dynamically
USB_POWER_PATH=""
if [ -d "/sys/class/net/can0/device" ]; then
    # Traverse up from can0 to find the USB device power control
    USB_POWER_PATH=$(readlink -f /sys/class/net/can0/device/../../power 2>/dev/null)
fi

if [ -n "$USB_POWER_PATH" ] && [ -d "$USB_POWER_PATH" ]; then
    echo -1 | sudo tee "$USB_POWER_PATH/autosuspend" > /dev/null 2>&1 && \
        echo "   ✓ Disabled USB autosuspend for CAN adapter"
    echo on | sudo tee "$USB_POWER_PATH/control" > /dev/null 2>&1 && \
        echo "   ✓ Set USB power control to 'on' for CAN adapter"
else
    echo "   Note: USB CAN adapter power path not found; skipping USB power configuration"
fi
echo "   ✓ Applied immediate fixes"

# Verify
echo ""
echo "=============================================="
echo "Verification"
echo "=============================================="

CURRENT_TXQUEUELEN=$(cat /sys/class/net/can0/tx_queue_len 2>/dev/null || echo "N/A")

# Dynamically find USB autosuspend value
if [ -n "$USB_POWER_PATH" ] && [ -f "$USB_POWER_PATH/autosuspend" ]; then
    CURRENT_AUTOSUSPEND=$(cat "$USB_POWER_PATH/autosuspend" 2>/dev/null || echo "N/A")
else
    CURRENT_AUTOSUSPEND="N/A (device path not found)"
fi

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
echo "  # Find USB power path dynamically:"
echo "  readlink -f /sys/class/net/can0/device/../../power/autosuspend"
echo "=============================================="
