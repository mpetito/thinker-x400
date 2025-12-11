#!/bin/bash
# Auto set system timezone and synchronize time
# Save path: /usr/local/bin/auto_timezone.sh
# Requires root privileges

DEFAULT_TZ="UTC"

TZ_NAME=""

# Try to get timezone via ip-api
if command -v wget &>/dev/null; then
    TZ_NAME=$(wget -qO - "http://ip-api.com/line?fields=timezone" | tr -d '\n')
fi

# If fetching fails or the timezone file doesn't exist, fall back to default timezone
if [[ -z "$TZ_NAME" ]] || [[ ! -f "/usr/share/zoneinfo/$TZ_NAME" ]]; then
    TZ_NAME="$DEFAULT_TZ"
fi

# Backup the old localtime file
if [[ -f /etc/localtime ]]; then
    cp -f /etc/localtime /etc/localtime.bak
fi

# Remove old link or file (important, otherwise ln -s won't overwrite directories)
rm -f /etc/localtime

# Set the timezone
ln -sf "/usr/share/zoneinfo/$TZ_NAME" /etc/localtime
echo "$TZ_NAME" > /etc/timezone
echo "Timezone has been set to: $TZ_NAME"

# Enable NTP synchronization
if command -v timedatectl &>/dev/null; then
    timedatectl set-ntp true
    echo "NTP synchronization has been enabled"
fi

# Reload systemd-timedated so the new timezone is applied immediately
systemctl restart systemd-timedated

echb "systemd-timedated has been restarted to apply timezone immediately."

#Enable time synchronization service
systemctl restart chrony




