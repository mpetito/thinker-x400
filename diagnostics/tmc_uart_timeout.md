# Eryone Thinker X400 - TMC UART Timeout Diagnostic Report

**Date of Incident:** December 27, 2025 (~10:00 AM)  
**Print Duration at Failure:** Approximately 62+ hours (similar to first failure)  
**Error Message:** "Timeout on wait for 'tmcuart_response' response"  
**Report Date:** December 27, 2025

---

## Executive Summary

A second long-duration print failed with a TMC UART timeout error. Analysis reveals the root cause is the CAN bus transmit queue length (`txqueuelen`) reverting to the default value of 128 instead of the required 1024. This causes CAN bus saturation during complex print moves, preventing TMC driver communication from completing within the timeout period.

**This is a different failure mode from the December 20th "verify_heater" error**, but may share the same underlying cause: CAN bus communication instability during extended prints.

---

## 1. Root Cause Analysis

### 1.1 The CAN txqueuelen Problem

| Parameter | Expected | Actual | Impact |
|-----------|----------|--------|--------|
| can0 txqueuelen | 1024 | 128 | 8× less buffer capacity |
| USB autosuspend | -1 (disabled) | 2 seconds | CAN adapter can suspend |

The fix from git commit `91221a6` ("increase the can buffer") IS present in `/etc/rc.local`:

```bash
echo makerbase | sudo -S ip link set can0 txqueuelen 1024
```

**However, the fix is lost when the USB CAN adapter reconnects.**

### 1.1.1 The USB Reconnect Problem (NEW FINDING)

From `dmesg`:

```
[ 1369.840449] gs_usb 1-1:1.0 can0: Couldn't shutdown device (err=-19)
[ 1370.620317] IPv6: ADDRCONF(NETDEV_CHANGE): can0: link becomes ready
[234023.787975] gs_usb 1-1:1.0 can0: Couldn't shutdown device (err=-19)
[234024.704890] IPv6: ADDRCONF(NETDEV_CHANGE): can0: link becomes ready
```

The USB CAN adapter (gs_usb) **reconnected twice**:

- At 1369 seconds (~23 minutes after boot)
- At 234023 seconds (~65 hours) - **THE EXACT MOMENT OF FAILURE**

When the USB device reconnects:

1. The `can0` interface is destroyed and recreated
2. The new interface gets the **default txqueuelen=128**
3. The rc.local fix (which ran at boot) is **NOT reapplied**
4. CAN bus saturates under load → TMC UART timeout

**USB autosuspend** (`autosuspend=2`) may be contributing to these disconnects by suspending the adapter during short idle periods between print moves (for example, between G-code moves, travel moves, or retractions).

### 1.2 Why txqueuelen Matters

The CAN bus on MKS SKIPR handles:

- Motion commands to the main MCU (STM32F407)
- Motion commands to EECAN toolhead (RP2040)
- TMC driver UART queries for stall detection/status
- Temperature sensor readings
- Heater PWM commands

During complex print moves (infill, curves, small details), the CAN bus traffic spikes. With `txqueuelen=128`:

1. Queue fills up quickly
2. New messages are delayed or dropped
3. TMC UART queries don't get responses in time
4. Klipper triggers "tmcuart_response timeout"
5. Emergency shutdown

### 1.3 Evidence from klippy.log.2025-12-26

The log file ends **abruptly mid-line**:

```
Stats 777755.6: gcodein=0  mcu: mcu_
```

This indicates the crash was so sudden that:

- The log buffer wasn't flushed to disk
- No shutdown message was recorded
- The error message was only shown on screen

**Last recorded statistics before crash:**

| Metric | Value | Notes |
|--------|-------|-------|
| print_time | 543,748 seconds | ~151 hours total runtime |
| sysload | 1.06 | Elevated (was 0.3-0.5) |
| memavail | 180,748 KB | Dropping rapidly |
| EECAN send_seq/receive_seq | 2987182/2987179 | 3 packets in flight |
| buffer_time | 2.4 seconds | Normal |
| extruder temp | 254.9°C | Stable |
| bed temp | 75.1°C | Stable |

**Memory was dropping rapidly** in the last few seconds:

- 201,616 KB → 193,580 KB → 185,120 KB → 180,968 KB → 180,748 KB
- This is ~5 MB/s memory consumption - indicative of CAN queue backup

---

## 2. Comparison with First Failure (Dec 20)

| Aspect | Dec 20 Failure | Dec 27 Failure |
|--------|---------------|----------------|
| Error Type | verify_heater | tmcuart_response |
| Component | Heater control | TMC driver comm |
| Duration | ~62 hours | ~62 hours |
| Log Capture | Truncated | Truncated mid-line |
| Temps Stable | Yes | Yes |
| CAN retransmits | High | Lower but present |
| txqueuelen | Unknown | Confirmed 128 |

**Hypothesis:** Both failures may stem from CAN bus instability. The first manifested as heater communication loss, the second as TMC UART timeout.

---

## 3. Solution

### 3.1 Immediate Fix (Manual)

SSH to the printer and run:

```bash
sudo ip link set can0 txqueuelen 1024
```

Verify with:

```bash
cat /sys/class/net/can0/tx_queue_len
# Should output: 1024
```

### 3.2 Permanent Fix (Udev Rules + Systemd Service)

The `rc.local` method fails when the USB CAN adapter reconnects. We need **udev rules** that trigger whenever `can0` is created.

**Files created:**

- `all/99-can-txqueuelen.rules` - Udev rule to set txqueuelen on can0 creation
- `all/99-usb-can-no-autosuspend.rules` - Udev rule to disable USB autosuspend
- `all/can-txqueuelen.service` - Systemd service (backup method)
- `all/install_can_txqueuelen.sh` - Installation script

**Installation:**

```bash
cd ~/thinker-x400/all
chmod +x install_can_txqueuelen.sh
./install_can_txqueuelen.sh
```

**What the udev rules do:**

1. When `can0` is created (boot OR USB reconnect): set txqueuelen=1024
2. When USB CAN adapter is added: disable autosuspend
3. These trigger automatically - no rc.local needed

### 3.3 Verification After Reboot

After rebooting, verify the fix persists:

```bash
cat /sys/class/net/can0/tx_queue_len
# Must show: 1024

systemctl status can-txqueuelen.service
# Should show: active (exited)

# Check USB autosuspend (path is system-specific, use this to find it):
cat $(readlink -f /sys/class/net/can0/device/../../power/autosuspend)
# Should show: -1
```

> **Note:** The USB device path (e.g., `1-1`, `1-2`, etc.) varies by system and USB port.
> Use the dynamic path detection shown above instead of hardcoding a specific path.

---

## 4. Additional Recommendations

### 4.1 Remove rc.local Entry (Optional)

If you installed the systemd service, you can remove the redundant rc.local entry:

```bash
sudo nano /etc/rc.local
# Remove the line: ifconfig can0 txqueuelen 1024
```

### 4.2 Monitor Future Prints

Create a monitoring script to log key metrics:

```bash
# Every 5 minutes during prints, log:
# - txqueuelen value
# - Memory available
# - CAN statistics from klippy.log
```

### 4.3 Consider Klipper CAN Parameters

In `printer.cfg`, these CAN-related settings can help:

```ini
[mcu]
canbus_uuid: <your_uuid>
# Increase if timing issues persist:
# canbus_timeout: 1.5

[mcu EECAN]
canbus_uuid: <your_uuid>
# Increase if timing issues persist:
# canbus_timeout: 1.5
```

---

## 5. Conclusion

The December 27 failure was caused by **insufficient CAN bus queue depth** (`txqueuelen=128` instead of `1024`). The fix was identified in commit `91221a6` but wasn't persisting across reboots.

Udev rules have been added as the primary mechanism to ensure the txqueuelen fix is applied both at boot and on USB reconnects, with a systemd service in place as a boot-time backup before Klipper starts. This should prevent future TMC UART timeout errors during long prints.

The December 20 "verify_heater" failure may have also been caused by CAN bus issues affecting heater temperature readings, though this cannot be confirmed without additional data.

---

## Appendix: Technical Details

### CAN Bus Architecture on MKS SKIPR

```
┌─────────────────────────────────────────────────────────┐
│                      RK3328 SoC                         │
│                    (Linux Host)                         │
│                         │                               │
│                    can0 interface                       │
│               (txqueuelen: 1024 required)               │
└─────────────────────────────────────────────────────────┘
                          │
                     CAN Bus (1 Mbps)
                          │
          ┌───────────────┴───────────────┐
          │                               │
┌─────────────────────┐      ┌─────────────────────┐
│   STM32F407 MCU     │      │   RP2040 EECAN      │
│   (Main Board)      │      │   (Toolhead)        │
│                     │      │                     │
│ - X/Y/Z steppers    │      │ - Extruder stepper  │
│ - TMC2209 (X,Y,Z)   │      │ - TMC2209 (E)       │
│ - Bed heater        │      │ - Hotend heater     │
│ - Fans              │      │ - Hotend thermistor │
│ - Probes            │      │ - Part cooling fan  │
└─────────────────────┘      └─────────────────────┘
```

### Systemd Service Ordering

```
systemd-modules-load.service
           │
           ▼
network-pre.target
           │
           ▼
can-txqueuelen.service  ◄── Sets txqueuelen=1024
           │
           ▼
klipper.service
           │
           ▼
moonraker.service
```
